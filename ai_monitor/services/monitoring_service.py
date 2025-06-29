import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import pandas as pd
import numpy as np

from core.database.base import get_db_context
from ai_monitor.models.database import (
    ModelMetric, DriftDetection, Alert, AlertSeverity, 
    ModelPerformance, DataQualityCheck
)
from ai_monitor.models.drift_detector import DriftDetectionEngine, DriftResult
from ai_monitor.collectors.data_collector import collection_engine, MetricData
from core.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MonitoringService:
    """Servicio principal de monitoreo de modelos"""
    
    def __init__(self):
        self.drift_detector = DriftDetectionEngine()
        self.active_monitors = {}  # model_id -> monitoring config
        self.is_running = False
        self.monitoring_task = None
    
    async def start_monitoring(
        self, 
        model_id: str, 
        drift_threshold: float = 0.05,
        check_interval_minutes: int = 15
    ):
        """Inicia monitoreo para un modelo específico"""
        
        monitor_config = {
            "model_id": model_id,
            "drift_threshold": drift_threshold,
            "check_interval_minutes": check_interval_minutes,
            "last_drift_check": None,
            "baseline_period_days": 7
        }
        
        self.active_monitors[model_id] = monitor_config
        
        # Iniciar recolección de métricas si no está activa
        if not collection_engine.is_running:
            await collection_engine.start_continuous_collection(
                model_ids=list(self.active_monitors.keys()),
                interval_seconds=60  # Recolectar cada minuto
            )
        
        # Iniciar task de monitoreo si no está activo
        if not self.is_running:
            await self._start_monitoring_loop()
        
        logger.info(f"Started monitoring for model {model_id}")
    
    async def stop_monitoring(self, model_id: str):
        """Detiene monitoreo para un modelo"""
        if model_id in self.active_monitors:
            del self.active_monitors[model_id]
            logger.info(f"Stopped monitoring for model {model_id}")
        
        # Si no hay más modelos, detener el loop
        if not self.active_monitors and self.is_running:
            await self._stop_monitoring_loop()
    
    async def _start_monitoring_loop(self):
        """Inicia el loop principal de monitoreo"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started monitoring loop")
    
    async def _stop_monitoring_loop(self):
        """Detiene el loop de monitoreo"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        await collection_engine.stop_continuous_collection()
        logger.info("Stopped monitoring loop")
    
    async def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        while self.is_running:
            try:
                # Procesar cada modelo monitoreado
                for model_id, config in self.active_monitors.items():
                    try:
                        await self._process_model_monitoring(model_id, config)
                    except Exception as e:
                        logger.error(f"Error monitoring model {model_id}: {e}")
                
                # Esperar antes del siguiente ciclo
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _process_model_monitoring(self, model_id: str, config: Dict[str, Any]):
        """Procesa monitoreo para un modelo específico"""
        now = datetime.utcnow()
        
        # Verificar si es hora de hacer drift check
        last_check = config.get("last_drift_check")
        interval_minutes = config["check_interval_minutes"]
        
        if last_check is None or (now - last_check).total_seconds() >= interval_minutes * 60:
            await self._check_model_drift(model_id, config)
            config["last_drift_check"] = now
        
        # Verificar alertas de performance
        await self._check_performance_alerts(model_id, config)
    
    async def _check_model_drift(self, model_id: str, config: Dict[str, Any]):
        """Ejecuta detección de drift para un modelo"""
        try:
            # Obtener datos de referencia (baseline)
            baseline_data = await self._get_baseline_data(
                model_id, 
                days_back=config["baseline_period_days"]
            )
            
            # Obtener datos actuales
            current_data = await self._get_recent_data(
                model_id,
                hours_back=1  # Última hora
            )
            
            if baseline_data.empty or current_data.empty:
                logger.warning(f"Insufficient data for drift detection on model {model_id}")
                return
            
            # Detectar drift en accuracy (métrica principal)
            accuracy_baseline = baseline_data[baseline_data['metric_type'] == 'accuracy']['value'].values
            accuracy_current = current_data[current_data['metric_type'] == 'accuracy']['value'].values
            
            if len(accuracy_baseline) > 10 and len(accuracy_current) > 5:
                drift_result = self.drift_detector.detect_feature_drift(
                    feature_name="accuracy",
                    reference_data=accuracy_baseline,
                    current_data=accuracy_current,
                    threshold=config["drift_threshold"]
                )
                
                # Guardar resultado en base de datos
                await self._save_drift_result(model_id, drift_result)
                
                # Crear alerta si se detectó drift
                if drift_result.is_drift_detected:
                    await self._create_drift_alert(model_id, drift_result)
            
        except Exception as e:
            logger.error(f"Error in drift detection for model {model_id}: {e}")
    
    async def _check_performance_alerts(self, model_id: str, config: Dict[str, Any]):
        """Verifica alertas de performance"""
        try:
            # Obtener métricas recientes
            recent_data = await self._get_recent_data(model_id, hours_back=0.5)  # Últimos 30min
            
            if recent_data.empty:
                return
            
            # Verificar umbrales críticos
            alerts_to_create = []
            
            # Error rate alto
            error_rates = recent_data[recent_data['metric_type'] == 'error_rate']['value']
            if not error_rates.empty and error_rates.mean() > 0.05:  # 5% threshold
                alerts_to_create.append({
                    "type": "high_error_rate",
                    "severity": AlertSeverity.HIGH,
                    "value": error_rates.mean(),
                    "threshold": 0.05,
                    "message": f"High error rate detected: {error_rates.mean():.3f}"
                })
            
            # Latencia alta
            latencies = recent_data[recent_data['metric_type'] == 'latency']['value']
            if not latencies.empty and latencies.mean() > 100:  # 100ms threshold
                alerts_to_create.append({
                    "type": "high_latency",
                    "severity": AlertSeverity.MEDIUM,
                    "value": latencies.mean(),
                    "threshold": 100,
                    "message": f"High latency detected: {latencies.mean():.1f}ms"
                })
            
            # Crear alertas
            for alert_data in alerts_to_create:
                await self._create_performance_alert(model_id, alert_data)
                
        except Exception as e:
            logger.error(f"Error checking performance alerts for model {model_id}: {e}")
    
    async def _get_baseline_data(self, model_id: str, days_back: int) -> pd.DataFrame:
        """Obtiene datos de baseline para comparación"""
        end_date = datetime.utcnow() - timedelta(days=1)  # Excluir último día
        start_date = end_date - timedelta(days=days_back)
        
        with get_db_context() as db:
            metrics = db.query(ModelMetric).filter(
                ModelMetric.model_id == model_id,
                ModelMetric.timestamp >= start_date,
                ModelMetric.timestamp <= end_date
            ).all()
            
            if not metrics:
                return pd.DataFrame()
            
            data = []
            for metric in metrics:
                data.append({
                    'metric_type': metric.metric_type,
                    'value': metric.value,
                    'timestamp': metric.timestamp
                })
            
            return pd.DataFrame(data)
    
    async def _get_recent_data(self, model_id: str, hours_back: float) -> pd.DataFrame:
        """Obtiene datos recientes"""
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        with get_db_context() as db:
            metrics = db.query(ModelMetric).filter(
                ModelMetric.model_id == model_id,
                ModelMetric.timestamp >= start_time
            ).all()
            
            if not metrics:
                return pd.DataFrame()
            
            data = []
            for metric in metrics:
                data.append({
                    'metric_type': metric.metric_type,
                    'value': metric.value,
                    'timestamp': metric.timestamp
                })
            
            return pd.DataFrame(data)
    
    async def _save_drift_result(self, model_id: str, drift_result: DriftResult):
        """Guarda resultado de drift en base de datos"""
        try:
            with get_db_context() as db:
                drift_detection = DriftDetection(
                    model_id=model_id,
                    feature_name=drift_result.feature_name,
                    drift_score=drift_result.drift_score,
                    threshold=drift_result.threshold,
                    is_drift_detected=drift_result.is_drift_detected,
                    algorithm=drift_result.algorithm,
                    reference_period_start=datetime.utcnow() - timedelta(days=7),
                    reference_period_end=datetime.utcnow() - timedelta(days=1),
                    detection_period_start=datetime.utcnow() - timedelta(hours=1),
                    detection_period_end=datetime.utcnow(),
                    statistics=drift_result.statistics
                )
                
                db.add(drift_detection)
                logger.info(f"Saved drift result for model {model_id}: drift={drift_result.is_drift_detected}")
                
        except Exception as e:
            logger.error(f"Error saving drift result: {e}")
    
    async def _create_drift_alert(self, model_id: str, drift_result: DriftResult):
        """Crea alerta de drift detectado"""
        try:
            with get_db_context() as db:
                alert = Alert(
                    model_id=model_id,
                    alert_type="drift_detected",
                    severity=AlertSeverity.HIGH.value,
                    title=f"Data drift detected in {drift_result.feature_name}",
                    message=f"Drift score: {drift_result.drift_score:.4f} (threshold: {drift_result.threshold})",
                    trigger_value=drift_result.drift_score,
                    threshold_value=drift_result.threshold,
                    context_data=drift_result.statistics
                )
                
                db.add(alert)
                logger.warning(f"Created drift alert for model {model_id}")
                
        except Exception as e:
            logger.error(f"Error creating drift alert: {e}")
    
    async def _create_performance_alert(self, model_id: str, alert_data: Dict[str, Any]):
        """Crea alerta de performance"""
        try:
            with get_db_context() as db:
                alert = Alert(
                    model_id=model_id,
                    alert_type=alert_data["type"],
                    severity=alert_data["severity"].value,
                    title=f"Performance issue: {alert_data['type']}",
                    message=alert_data["message"],
                    trigger_value=alert_data["value"],
                    threshold_value=alert_data["threshold"]
                )
                
                db.add(alert)
                logger.warning(f"Created performance alert for model {model_id}: {alert_data['type']}")
                
        except Exception as e:
            logger.error(f"Error creating performance alert: {e}")
    
    async def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """Obtiene status actual de un modelo"""
        try:
            with get_db_context() as db:
                # Obtener métricas recientes
                recent_metrics = db.query(ModelMetric).filter(
                    ModelMetric.model_id == model_id,
                    ModelMetric.timestamp >= datetime.utcnow() - timedelta(hours=1)
                ).all()
                
                # Obtener alertas activas
                active_alerts = db.query(Alert).filter(
                    Alert.model_id == model_id,
                    Alert.is_active == True
                ).all()
                
                # Obtener último drift detection
                last_drift = db.query(DriftDetection).filter(
                    DriftDetection.model_id == model_id
                ).order_by(desc(DriftDetection.timestamp)).first()
                
                # Procesar métricas
                metrics_summary = {}
                for metric in recent_metrics:
                    if metric.metric_type not in metrics_summary:
                        metrics_summary[metric.metric_type] = []
                    metrics_summary[metric.metric_type].append(metric.value)
                
                # Calcular promedios
                metrics_avg = {}
                for metric_type, values in metrics_summary.items():
                    metrics_avg[metric_type] = np.mean(values) if values else None
                
                return {
                    "model_id": model_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": metrics_avg,
                    "active_alerts": len(active_alerts),
                    "last_drift_check": last_drift.timestamp.isoformat() if last_drift else None,
                    "drift_detected": last_drift.is_drift_detected if last_drift else False,
                    "monitoring_active": model_id in self.active_monitors
                }
                
        except Exception as e:
            logger.error(f"Error getting model status: {e}")
            return {"error": str(e)}
    
    def get_monitored_models(self) -> List[str]:
        """Retorna lista de modelos siendo monitoreados"""
        return list(self.active_monitors.keys())


# Instancia global del servicio de monitoreo
monitoring_service = MonitoringService() 
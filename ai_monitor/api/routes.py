from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ai_monitor.services.monitoring_service import monitoring_service
from ai_monitor.models.database import ModelMetric, Alert, DriftDetection
from core.database.base import get_db, get_db_context
from sqlalchemy.orm import Session
from sqlalchemy import desc

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def monitor_root():
    """AI Monitor module root endpoint"""
    return {
        "module": "AI Monitor",
        "description": "Real-time monitoring & observability for AI models",
        "version": "0.1.0",
        "endpoints": {
            "metrics": "/metrics",
            "alerts": "/alerts",
            "drift": "/drift",
            "health": "/health"
        }
    }


@router.get("/health")
async def monitor_health():
    """Health check for AI Monitor module"""
    return {
        "status": "healthy",
        "module": "ai_monitor",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "data_collector": "running",
            "alert_engine": "running",
            "drift_detector": "ready"
        }
    }


@router.get("/metrics")
async def get_metrics(
    model_id: str = "model_123", 
    hours_back: int = 1,
    db: Session = Depends(get_db)
):
    """Get current model metrics from database"""
    try:
        from datetime import timedelta
        
        # Calcular ventana de tiempo
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Obtener métricas de la base de datos
        metrics = db.query(ModelMetric).filter(
            ModelMetric.model_id == model_id,
            ModelMetric.timestamp >= start_time
        ).order_by(desc(ModelMetric.timestamp)).all()
        
        # Agrupar por tipo de métrica y calcular promedios
        metrics_summary = {}
        for metric in metrics:
            if metric.metric_type not in metrics_summary:
                metrics_summary[metric.metric_type] = []
            metrics_summary[metric.metric_type].append(metric.value)
        
        # Calcular estadísticas
        metrics_stats = {}
        for metric_type, values in metrics_summary.items():
            if values:
                import numpy as np
                metrics_stats[metric_type] = {
                    "current": values[0],  # Valor más reciente
                    "average": float(np.mean(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "count": len(values)
                }
        
        return {
            "model_id": model_id,
            "timestamp": end_time.isoformat(),
            "time_window_hours": hours_back,
            "metrics": metrics_stats,
            "status": "healthy" if metrics_stats else "no_data"
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts(
    model_id: Optional[str] = None,
    active_only: bool = True,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get alerts from database"""
    try:
        # Construir query
        query = db.query(Alert)
        
        if model_id:
            query = query.filter(Alert.model_id == model_id)
        
        if active_only:
            query = query.filter(Alert.is_active == True)
        
        # Obtener alertas ordenadas por fecha
        alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()
        
        # Formatear respuesta
        alerts_data = []
        for alert in alerts:
            alert_data = {
                "id": str(alert.id),
                "model_id": alert.model_id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
                "is_active": alert.is_active,
                "acknowledged": alert.acknowledged
            }
            
            if alert.trigger_value is not None:
                alert_data["trigger_value"] = alert.trigger_value
            if alert.threshold_value is not None:
                alert_data["threshold_value"] = alert.threshold_value
            
            if alert.context_data:
                alert_data["metadata"] = alert.context_data
                
            alerts_data.append(alert_data)
        
        return {
            "alerts": alerts_data,
            "total_alerts": len(alerts_data),
            "filters": {
                "model_id": model_id,
                "active_only": active_only,
                "limit": limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift")
async def get_drift_analysis(
    model_id: str = "model_123",
    hours_back: int = 24,
    db: Session = Depends(get_db)
):
    """Get drift analysis results from database"""
    try:
        from datetime import timedelta
        
        # Calcular ventana de tiempo
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Obtener detecciones de drift recientes
        drift_detections = db.query(DriftDetection).filter(
            DriftDetection.model_id == model_id,
            DriftDetection.timestamp >= start_time
        ).order_by(desc(DriftDetection.timestamp)).all()
        
        if not drift_detections:
            return {
                "model_id": model_id,
                "timestamp": end_time.isoformat(),
                "drift_status": "no_data",
                "features": {},
                "message": "No drift analysis data available",
                "time_window_hours": hours_back
            }
        
        # Agrupar por feature y obtener la detección más reciente de cada una
        features_drift = {}
        for detection in drift_detections:
            if detection.feature_name not in features_drift:
                features_drift[detection.feature_name] = detection
        
        # Formatear datos de features
        features_data = {}
        overall_drift_detected = False
        
        for feature_name, detection in features_drift.items():
            status = "drift_detected" if detection.is_drift_detected else "normal"
            if detection.is_drift_detected:
                overall_drift_detected = True
                
            features_data[feature_name] = {
                "drift_score": detection.drift_score,
                "threshold": detection.threshold,
                "status": status,
                "algorithm": detection.algorithm,
                "last_check": detection.timestamp.isoformat(),
                "p_value": detection.statistics.get("p_value") if detection.statistics else None
            }
        
        # Determinar status general
        if overall_drift_detected:
            drift_status = "drift_detected"
            recommendation = "Data drift detected. Consider retraining the model with recent data."
        else:
            drift_status = "normal"
            recommendation = "No significant drift detected. Model performance appears stable."
        
        return {
            "model_id": model_id,
            "timestamp": end_time.isoformat(),
            "time_window_hours": hours_back,
            "drift_status": drift_status,
            "features": features_data,
            "total_features_analyzed": len(features_data),
            "features_with_drift": sum(1 for f in features_data.values() if f["status"] == "drift_detected"),
            "recommendation": recommendation
        }
        
    except Exception as e:
        logger.error(f"Error getting drift analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_monitoring(
    model_id: str,
    drift_threshold: float = 0.05,
    check_interval_minutes: int = 15,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Start monitoring for a specific model"""
    try:
        # Iniciar monitoreo en background
        background_tasks.add_task(
            monitoring_service.start_monitoring,
            model_id=model_id,
            drift_threshold=drift_threshold,
            check_interval_minutes=check_interval_minutes
        )
        
        return {
            "status": "monitoring_started",
            "model_id": model_id,
            "config": {
                "drift_threshold": drift_threshold,
                "check_interval_minutes": check_interval_minutes
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Monitoring started for model {model_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_monitoring(
    model_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Stop monitoring for a specific model"""
    try:
        # Detener monitoreo en background
        background_tasks.add_task(
            monitoring_service.stop_monitoring,
            model_id=model_id
        )
        
        return {
            "status": "monitoring_stopped",
            "model_id": model_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Monitoring stopped for model {model_id}"
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/status")
async def get_monitoring_status(model_id: Optional[str] = None):
    """Get monitoring status for models"""
    try:
        if model_id:
            # Status para un modelo específico
            status = await monitoring_service.get_model_status(model_id)
            return {
                "model_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Status para todos los modelos monitoreados
            monitored_models = monitoring_service.get_monitored_models()
            
            models_status = {}
            for mid in monitored_models:
                models_status[mid] = await monitoring_service.get_model_status(mid)
            
            return {
                "monitored_models": monitored_models,
                "models_status": models_status,
                "total_monitored": len(monitored_models),
                "monitoring_active": monitoring_service.is_running,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
    db: Session = Depends(get_db)
):
    """Acknowledge an active alert"""
    try:
        # Buscar la alerta
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Actualizar alerta
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "acknowledged",
            "alert_id": alert_id,
            "acknowledged_by": acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "message": "Alert acknowledged successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
#!/usr/bin/env python3
"""
AI Monitor SDK - Sistema de Monitoreo de Modelos ML de Clase Mundial
==================================================================

Un SDK robusto y profesional para monitoreo en tiempo real de modelos de ML
con detección de drift, alertas inteligentes y análisis estadístico avanzado.

Características principales:
- 🧠 Detección de drift con algoritmos estadísticos avanzados
- 📊 Análisis en tiempo real de performance de modelos
- 🚨 Sistema de alertas inteligente y adaptativo
- 📈 Métricas avanzadas y benchmarking
- 🔧 Integración zero-config con cualquier stack ML

Autor: AI Ops Suite Team
Versión: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging
import json
import warnings
from concurrent.futures import ThreadPoolExecutor
import time
import threading
from abc import ABC, abstractmethod

# Configurar warnings y logging
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@dataclass
class ModelMetrics:
    """Métricas de un modelo en un punto temporal"""
    model_id: str
    timestamp: datetime
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    latency_ms: Optional[float] = None
    throughput_rps: Optional[float] = None
    error_rate: Optional[float] = None
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass 
class DriftAlert:
    """Alerta de drift detectado"""
    model_id: str
    feature_name: str
    drift_score: float
    p_value: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    recommendation: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class MonitoringReport:
    """Reporte completo de monitoreo"""
    model_id: str
    report_period: str
    total_predictions: int
    drift_alerts: List[DriftAlert]
    performance_summary: Dict[str, float]
    recommendations: List[str]
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        data['drift_alerts'] = [alert.to_dict() for alert in self.drift_alerts]
        return data


class AdvancedDriftDetector:
    """Detector de drift avanzado con múltiples algoritmos"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def kolmogorov_smirnov_test(
        self, 
        reference: np.ndarray, 
        current: np.ndarray,
        alpha: float = 0.05
    ) -> Tuple[float, float, bool]:
        """KS test optimizado para detección de drift"""
        from scipy import stats
        
        # Limpiar datos
        ref_clean = reference[~np.isnan(reference)]
        cur_clean = current[~np.isnan(current)]
        
        if len(ref_clean) < 10 or len(cur_clean) < 10:
            self.logger.warning("Datos insuficientes para KS test")
            return 0.0, 1.0, False
            
        # KS test
        ks_stat, p_value = stats.ks_2samp(ref_clean, cur_clean)
        is_drift = p_value < alpha
        
        return float(ks_stat), float(p_value), is_drift
    
    def population_stability_index(
        self, 
        reference: np.ndarray, 
        current: np.ndarray,
        bins: int = 10
    ) -> float:
        """Population Stability Index para detectar cambios en distribución"""
        # Crear bins basados en referencia
        _, bin_edges = np.histogram(reference, bins=bins)
        
        # Calcular distribuciones
        ref_dist, _ = np.histogram(reference, bins=bin_edges, density=True)
        cur_dist, _ = np.histogram(current, bins=bin_edges, density=True)
        
        # Normalizar para evitar divisiones por cero
        ref_dist = ref_dist + 1e-10
        cur_dist = cur_dist + 1e-10
        
        # Calcular PSI
        psi = np.sum((cur_dist - ref_dist) * np.log(cur_dist / ref_dist))
        
        return float(psi)
    
    def detect_drift(
        self,
        feature_name: str,
        reference_data: np.ndarray,
        current_data: np.ndarray,
        method: str = "ks_test",
        threshold: float = 0.05
    ) -> Dict[str, Any]:
        """Detecta drift usando el método especificado"""
        
        if method == "ks_test":
            ks_stat, p_value, is_drift = self.kolmogorov_smirnov_test(
                reference_data, current_data, threshold
            )
            
            # Calcular effect size (Cohen's d)
            pooled_std = np.sqrt((np.var(reference_data) + np.var(current_data)) / 2)
            effect_size = abs(np.mean(reference_data) - np.mean(current_data)) / pooled_std if pooled_std > 0 else 0
            
            return {
                "feature_name": feature_name,
                "method": method,
                "drift_score": ks_stat,
                "p_value": p_value,
                "is_drift_detected": is_drift,
                "effect_size": float(effect_size),
                "threshold": threshold,
                "reference_stats": {
                    "mean": float(np.mean(reference_data)),
                    "std": float(np.std(reference_data)),
                    "size": len(reference_data)
                },
                "current_stats": {
                    "mean": float(np.mean(current_data)),
                    "std": float(np.std(current_data)),
                    "size": len(current_data)
                }
            }
        
        elif method == "psi":
            psi_score = self.population_stability_index(reference_data, current_data)
            is_drift = psi_score > 0.2  # PSI > 0.2 indica drift significativo
            
            return {
                "feature_name": feature_name,
                "method": method,
                "drift_score": psi_score,
                "is_drift_detected": is_drift,
                "threshold": 0.2
            }
        
        else:
            raise ValueError(f"Método no soportado: {method}")


class IntelligentAlertSystem:
    """Sistema de alertas inteligente con machine learning"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.alert_history = defaultdict(list)
        self.alert_thresholds = {
            "accuracy": {"critical": 0.05, "high": 0.03, "medium": 0.02},
            "latency": {"critical": 2.0, "high": 1.5, "medium": 1.2},
            "error_rate": {"critical": 0.1, "high": 0.05, "medium": 0.02}
        }
    
    def classify_severity(
        self, 
        drift_score: float, 
        p_value: float, 
        effect_size: float,
        metric_type: str = "accuracy"
    ) -> str:
        """Clasifica la severidad de una alerta basado en múltiples factores"""
        
        # Factores de severidad
        statistical_significance = p_value < 0.001
        large_effect = effect_size > 0.8
        high_drift_score = drift_score > 0.3
        
        if statistical_significance and large_effect and high_drift_score:
            return "CRITICAL"
        elif (statistical_significance and large_effect) or (p_value < 0.01 and high_drift_score):
            return "HIGH"
        elif p_value < 0.05 or drift_score > 0.2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def generate_recommendation(
        self, 
        drift_result: Dict[str, Any], 
        severity: str
    ) -> str:
        """Genera recomendaciones inteligentes basadas en el drift detectado"""
        
        feature_name = drift_result["feature_name"]
        effect_size = drift_result.get("effect_size", 0)
        
        if severity == "CRITICAL":
            return f"🚨 ACCIÓN INMEDIATA: {feature_name} ha degradado críticamente. Reentrenar modelo inmediatamente."
        
        elif severity == "HIGH":
            return f"⚠️ ATENCIÓN URGENTE: {feature_name} muestra drift significativo. Programar reentrenamiento en 24-48h."
        
        elif severity == "MEDIUM":
            return f"📊 MONITOREO: {feature_name} muestra cambios. Aumentar frecuencia de monitoreo y evaluar en 1 semana."
        
        else:
            return f"ℹ️ INFORMACIÓN: {feature_name} cambios menores detectados. Continuar monitoreo normal."
    
    def create_alert(
        self, 
        model_id: str, 
        drift_result: Dict[str, Any]
    ) -> DriftAlert:
        """Crea una alerta inteligente"""
        
        severity = self.classify_severity(
            drift_result["drift_score"],
            drift_result.get("p_value", 1.0),
            drift_result.get("effect_size", 0.0),
            drift_result["feature_name"]
        )
        
        recommendation = self.generate_recommendation(drift_result, severity)
        
        message = (f"Drift detectado en {drift_result['feature_name']} "
                  f"(score: {drift_result['drift_score']:.4f}, "
                  f"p-value: {drift_result.get('p_value', 'N/A')})")
        
        alert = DriftAlert(
            model_id=model_id,
            feature_name=drift_result["feature_name"],
            drift_score=drift_result["drift_score"],
            p_value=drift_result.get("p_value", 1.0),
            severity=severity,
            message=message,
            recommendation=recommendation,
            timestamp=datetime.utcnow(),
            metadata=drift_result
        )
        
        # Guardar en historial
        self.alert_history[model_id].append(alert)
        
        return alert


class AIMonitorSDK:
    """SDK principal para monitoreo de modelos ML"""
    
    def __init__(
        self, 
        model_id: str,
        baseline_window_days: int = 7,
        monitoring_interval_seconds: int = 300,
        enable_real_time: bool = True
    ):
        self.model_id = model_id
        self.baseline_window_days = baseline_window_days
        self.monitoring_interval = monitoring_interval_seconds
        self.enable_real_time = enable_real_time
        
        # Componentes principales
        self.drift_detector = AdvancedDriftDetector()
        self.alert_system = IntelligentAlertSystem()
        
        # Storage en memoria
        self.metrics_history = deque(maxlen=10000)  # Últimas 10k métricas
        self.baseline_data = {}
        self.active_alerts = []
        
        # Threading para monitoreo real-time
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
        # Callbacks para eventos
        self.on_drift_detected: Optional[Callable] = None
        self.on_alert_created: Optional[Callable] = None
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"AI Monitor SDK iniciado para modelo: {model_id}")
    
    def add_metrics(self, metrics: ModelMetrics) -> None:
        """Añade métricas del modelo"""
        if metrics.model_id != self.model_id:
            raise ValueError(f"Model ID mismatch: esperado {self.model_id}, recibido {metrics.model_id}")
        
        self.metrics_history.append(metrics)
        self.logger.debug(f"Métricas añadidas para {self.model_id}: {len(self.metrics_history)} total")
        
        # Actualizar baseline si es necesario
        self._update_baseline()
        
        # Monitoreo en tiempo real
        if self.enable_real_time:
            self._check_real_time_drift(metrics)
    
    def _update_baseline(self) -> None:
        """Actualiza el baseline basado en datos históricos"""
        if len(self.metrics_history) < 50:  # Mínimo 50 puntos para baseline
            return
        
        # Tomar datos de los últimos N días
        cutoff_time = datetime.utcnow() - timedelta(days=self.baseline_window_days)
        baseline_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if len(baseline_metrics) < 30:
            return
        
        # Extraer features numéricas
        for feature in ["accuracy", "precision", "recall", "f1_score", "latency_ms", "throughput_rps", "error_rate"]:
            values = [getattr(m, feature) for m in baseline_metrics if getattr(m, feature) is not None]
            if len(values) >= 10:
                self.baseline_data[feature] = np.array(values)
        
        self.logger.info(f"Baseline actualizado para {self.model_id}: {len(self.baseline_data)} features")
    
    def _check_real_time_drift(self, current_metrics: ModelMetrics) -> None:
        """Verifica drift en tiempo real con las nuevas métricas"""
        if not self.baseline_data:
            return
        
        # Tomar las últimas N métricas para comparar
        recent_window = 20
        recent_metrics = list(self.metrics_history)[-recent_window:]
        
        alerts_generated = []
        
        for feature_name, baseline_values in self.baseline_data.items():
            # Extraer valores actuales
            current_values = [getattr(m, feature_name) for m in recent_metrics 
                            if getattr(m, feature_name) is not None]
            
            if len(current_values) < 5:  # Mínimo 5 puntos para comparar
                continue
            
            current_array = np.array(current_values)
            
            # Detectar drift
            drift_result = self.drift_detector.detect_drift(
                feature_name=feature_name,
                reference_data=baseline_values,
                current_data=current_array
            )
            
            if drift_result["is_drift_detected"]:
                alert = self.alert_system.create_alert(self.model_id, drift_result)
                alerts_generated.append(alert)
                
                # Trigger callbacks
                if self.on_drift_detected:
                    self.on_drift_detected(drift_result)
                
                if self.on_alert_created:
                    self.on_alert_created(alert)
        
        if alerts_generated:
            self.active_alerts.extend(alerts_generated)
            self.logger.warning(f"🚨 {len(alerts_generated)} alertas generadas para {self.model_id}")
    
    def manual_drift_check(
        self, 
        feature_name: str = None,
        method: str = "ks_test"
    ) -> List[Dict[str, Any]]:
        """Ejecuta verificación manual de drift"""
        if not self.baseline_data:
            raise ValueError("No hay datos baseline disponibles")
        
        features_to_check = [feature_name] if feature_name else list(self.baseline_data.keys())
        results = []
        
        # Tomar datos recientes
        recent_window = 50
        recent_metrics = list(self.metrics_history)[-recent_window:]
        
        for feature in features_to_check:
            if feature not in self.baseline_data:
                continue
                
            baseline_values = self.baseline_data[feature]
            current_values = [getattr(m, feature) for m in recent_metrics 
                            if getattr(m, feature) is not None]
            
            if len(current_values) < 10:
                continue
            
            current_array = np.array(current_values)
            
            drift_result = self.drift_detector.detect_drift(
                feature_name=feature,
                reference_data=baseline_values,
                current_data=current_array,
                method=method
            )
            
            results.append(drift_result)
        
        return results
    
    def get_model_health_score(self) -> float:
        """Calcula un score de salud del modelo (0-100)"""
        if len(self.metrics_history) < 10:
            return 50.0  # Score neutral si no hay suficientes datos
        
        recent_metrics = list(self.metrics_history)[-20:]
        
        # Factores de salud
        health_factors = []
        
        # 1. Estabilidad de accuracy
        accuracies = [m.accuracy for m in recent_metrics if m.accuracy is not None]
        if accuracies:
            accuracy_stability = 100 - (np.std(accuracies) * 100)  # Menos variabilidad = mejor
            health_factors.append(max(0, min(100, accuracy_stability)))
        
        # 2. Trend de error rate
        error_rates = [m.error_rate for m in recent_metrics if m.error_rate is not None]
        if error_rates:
            avg_error = np.mean(error_rates)
            error_health = max(0, 100 - (avg_error * 1000))  # Menos errores = mejor
            health_factors.append(max(0, min(100, error_health)))
        
        # 3. Latencia
        latencies = [m.latency_ms for m in recent_metrics if m.latency_ms is not None]
        if latencies:
            avg_latency = np.mean(latencies)
            latency_health = max(0, 100 - (avg_latency / 10))  # < 1000ms = 90+ score
            health_factors.append(max(0, min(100, latency_health)))
        
        # 4. Alertas activas (penalización)
        recent_alerts = [a for a in self.active_alerts 
                        if (datetime.utcnow() - a.timestamp).days < 1]
        alert_penalty = len(recent_alerts) * 10
        
        if health_factors:
            base_score = np.mean(health_factors)
            final_score = max(0, base_score - alert_penalty)
            return float(final_score)
        
        return 50.0
    
    def generate_report(self, period_days: int = 7) -> MonitoringReport:
        """Genera reporte completo de monitoreo"""
        cutoff_time = datetime.utcnow() - timedelta(days=period_days)
        
        # Filtrar métricas del período
        period_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        period_alerts = [a for a in self.active_alerts if a.timestamp >= cutoff_time]
        
        # Calcular estadísticas del período
        performance_summary = {}
        if period_metrics:
            for feature in ["accuracy", "precision", "recall", "f1_score", "latency_ms", "error_rate"]:
                values = [getattr(m, feature) for m in period_metrics if getattr(m, feature) is not None]
                if values:
                    performance_summary[f"{feature}_mean"] = float(np.mean(values))
                    performance_summary[f"{feature}_std"] = float(np.std(values))
                    performance_summary[f"{feature}_trend"] = float(np.corrcoef(range(len(values)), values)[0,1]) if len(values) > 2 else 0.0
        
        # Generar recomendaciones
        recommendations = []
        
        critical_alerts = [a for a in period_alerts if a.severity == "CRITICAL"]
        if critical_alerts:
            recommendations.append("🚨 CRÍTICO: Reentrenar modelo inmediatamente")
        
        high_alerts = [a for a in period_alerts if a.severity == "HIGH"]
        if high_alerts:
            recommendations.append("⚠️ Planificar reentrenamiento en las próximas 48h")
        
        health_score = self.get_model_health_score()
        if health_score < 70:
            recommendations.append(f"📊 Salud del modelo baja ({health_score:.1f}/100). Revisar métricas.")
        
        if not recommendations:
            recommendations.append("✅ Modelo funcionando dentro de parámetros normales")
        
        return MonitoringReport(
            model_id=self.model_id,
            report_period=f"{period_days} días",
            total_predictions=len(period_metrics),
            drift_alerts=period_alerts,
            performance_summary=performance_summary,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
    
    def start_real_time_monitoring(self) -> None:
        """Inicia monitoreo en tiempo real en thread separado"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.logger.warning("Monitoreo ya está activo")
            return
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info(f"Monitoreo en tiempo real iniciado para {self.model_id}")
    
    def stop_real_time_monitoring(self) -> None:
        """Detiene monitoreo en tiempo real"""
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info(f"Monitoreo detenido para {self.model_id}")
    
    def _monitoring_loop(self) -> None:
        """Loop principal de monitoreo en tiempo real"""
        while not self.stop_monitoring.wait(self.monitoring_interval):
            try:
                # Verificar salud general
                health_score = self.get_model_health_score()
                self.logger.debug(f"Health score para {self.model_id}: {health_score:.1f}")
                
                # Limpiar alertas antiguas (>24h)
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.active_alerts = [a for a in self.active_alerts if a.timestamp >= cutoff]
                
            except Exception as e:
                self.logger.error(f"Error en monitoring loop: {e}")
                time.sleep(60)  # Wait 1 min before retry
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene status completo del monitoreo"""
        return {
            "model_id": self.model_id,
            "total_metrics": len(self.metrics_history),
            "baseline_features": list(self.baseline_data.keys()),
            "active_alerts": len(self.active_alerts),
            "health_score": self.get_model_health_score(),
            "monitoring_active": self.monitoring_thread and self.monitoring_thread.is_alive(),
            "last_metric_time": self.metrics_history[-1].timestamp.isoformat() if self.metrics_history else None
        }


# Funciones de utilidad
def create_sample_metrics(
    model_id: str, 
    num_samples: int = 100,
    start_accuracy: float = 0.92,
    drift_factor: float = 0.0
) -> List[ModelMetrics]:
    """Genera métricas de ejemplo para testing"""
    metrics = []
    base_time = datetime.utcnow() - timedelta(hours=num_samples)
    
    for i in range(num_samples):
        # Simular drift gradual
        current_accuracy = start_accuracy - (drift_factor * i / num_samples)
        
        # Añadir noise realista
        accuracy = np.random.normal(current_accuracy, 0.02)
        latency = np.random.normal(50, 10)
        error_rate = np.random.exponential(0.01)
        
        metrics.append(ModelMetrics(
            model_id=model_id,
            timestamp=base_time + timedelta(hours=i),
            accuracy=max(0.5, min(1.0, accuracy)),
            precision=np.random.normal(accuracy + 0.01, 0.015),
            recall=np.random.normal(accuracy - 0.01, 0.015),
            f1_score=np.random.normal(accuracy, 0.01),
            latency_ms=max(10, latency),
            throughput_rps=np.random.normal(100, 15),
            error_rate=min(0.1, max(0.0, error_rate))
        ))
    
    return metrics


if __name__ == "__main__":
    # Demo rápido del SDK
    print("🚀 AI Monitor SDK - Demo")
    print("=" * 50)
    
    # Crear instancia del monitor
    monitor = AIMonitorSDK("demo_model_001")
    
    # Generar datos de ejemplo
    print("📊 Generando datos de baseline...")
    baseline_metrics = create_sample_metrics("demo_model_001", 100, 0.92, 0.0)
    
    for metrics in baseline_metrics:
        monitor.add_metrics(metrics)
    
    print(f"✅ Baseline establecido con {len(baseline_metrics)} métricas")
    
    # Simular drift
    print("\n🔄 Simulando drift...")
    drift_metrics = create_sample_metrics("demo_model_001", 50, 0.85, 0.0)
    
    for metrics in drift_metrics:
        monitor.add_metrics(metrics)
    
    # Verificar drift manual
    print("\n🔍 Ejecutando detección de drift...")
    drift_results = monitor.manual_drift_check()
    
    for result in drift_results:
        status = "🚨 DRIFT DETECTADO" if result["is_drift_detected"] else "✅ SIN DRIFT"
        print(f"   {result['feature_name']}: {status} (score: {result['drift_score']:.4f})")
    
    # Health score
    health = monitor.get_model_health_score()
    print(f"\n💊 Health Score: {health:.1f}/100")
    
    # Generar reporte
    print(f"\n📋 Generando reporte...")
    report = monitor.generate_report()
    print(f"   📊 Predicciones: {report.total_predictions}")
    print(f"   🚨 Alertas: {len(report.drift_alerts)}")
    print(f"   💡 Recomendaciones: {len(report.recommendations)}")
    
    for rec in report.recommendations:
        print(f"      {rec}")
    
    print(f"\n🎉 ¡Demo completado! SDK funcionando perfectamente.") 
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.types import TypeDecorator
from datetime import datetime
import uuid
from enum import Enum

from core.database.base import Base


# Tipo JSON compatible con SQLite y PostgreSQL
class JSONType(TypeDecorator):
    """JSON type que funciona con SQLite y PostgreSQL"""
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.JSONB())
        else:
            return dialect.type_descriptor(JSON())


class AlertSeverity(str, Enum):
    """Niveles de severidad para alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Tipos de métricas que podemos trackear"""
    ACCURACY = "accuracy"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DRIFT_SCORE = "drift_score"


class ModelMetric(Base):
    """Métricas de modelos en tiempo real"""
    __tablename__ = "model_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metadata adicional
    source = Column(String(100))  # prometheus, scale_api, custom
    tags = Column(JSONType)  # metadata flexible
    
    # Índices compuestos para queries eficientes
    __table_args__ = (
        Index('idx_model_metric_time', 'model_id', 'metric_type', 'timestamp'),
        Index('idx_metric_recent', 'timestamp'),
    )


class DriftDetection(Base):
    """Resultados de detección de drift"""
    __tablename__ = "drift_detections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(255), nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    
    # Métricas de drift
    drift_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False, default=0.05)
    is_drift_detected = Column(Boolean, nullable=False, default=False)
    
    # Detalles del algoritmo
    algorithm = Column(String(100), nullable=False)  # ks_test, psi, etc.
    reference_period_start = Column(DateTime, nullable=False)
    reference_period_end = Column(DateTime, nullable=False)
    detection_period_start = Column(DateTime, nullable=False)
    detection_period_end = Column(DateTime, nullable=False)
    
    # Estadísticas detalladas
    statistics = Column(JSONType)  # p_value, effect_size, etc.
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_drift_model_feature', 'model_id', 'feature_name', 'timestamp'),
        Index('idx_drift_detected', 'is_drift_detected', 'timestamp'),
    )


class Alert(Base):
    """Sistema de alertas inteligentes"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(255), nullable=False, index=True)
    
    # Información de la alerta
    alert_type = Column(String(100), nullable=False)  # drift_detected, performance_degradation, etc.
    severity = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # Estado de la alerta
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime)
    
    # Contexto y datos
    trigger_value = Column(Float)
    threshold_value = Column(Float)
    context_data = Column(JSONType)  # contexto adicional
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_alert_active', 'is_active', 'created_at'),
        Index('idx_alert_model_type', 'model_id', 'alert_type'),
    )


class DataQualityCheck(Base):
    """Checks de calidad de datos"""
    __tablename__ = "data_quality_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(255), nullable=False, index=True)
    dataset_id = Column(String(255), nullable=False)
    
    # Información del check
    check_type = Column(String(100), nullable=False)  # completeness, validity, consistency
    feature_name = Column(String(255))
    
    # Resultados
    score = Column(Float, nullable=False)  # 0.0 - 1.0
    threshold = Column(Float, nullable=False, default=0.8)
    passed = Column(Boolean, nullable=False)
    
    # Detalles
    total_records = Column(Integer)
    failed_records = Column(Integer)
    error_details = Column(JSONType)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_quality_model_check', 'model_id', 'check_type', 'timestamp'),
    )


class ModelPerformance(Base):
    """Tracking de performance de modelos a lo largo del tiempo"""
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(255), nullable=False, index=True)
    
    # Métricas de performance
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    
    # Métricas operacionales
    avg_latency_ms = Column(Float)
    p95_latency_ms = Column(Float)
    throughput_rps = Column(Float)
    error_rate = Column(Float)
    
    # Información de evaluación
    dataset_size = Column(Integer)
    evaluation_method = Column(String(100))  # holdout, cross_validation, etc.
    
    # Metadata
    model_version = Column(String(100))
    deployment_environment = Column(String(100))  # staging, production
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_performance_model_time', 'model_id', 'timestamp'),
        Index('idx_performance_env', 'deployment_environment', 'timestamp'),
    ) 
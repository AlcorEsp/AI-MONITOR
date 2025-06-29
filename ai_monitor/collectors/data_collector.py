import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import aiohttp
import json
from prometheus_client.parser import text_string_to_metric_families
from sqlalchemy.orm import Session

from core.database.base import get_db_context
from ai_monitor.models.database import ModelMetric, MetricType
from core.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class MetricData:
    """Estructura de datos para métricas"""
    model_id: str
    metric_type: str
    value: float
    timestamp: datetime
    source: str
    tags: Optional[Dict[str, Any]] = None


class DataSource(ABC):
    """Base class para fuentes de datos"""
    
    @abstractmethod
    async def collect_metrics(self, model_id: str) -> List[MetricData]:
        """Recolecta métricas de esta fuente"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Retorna el nombre de la fuente"""
        pass


class PrometheusDataSource(DataSource):
    """Colector de métricas desde Prometheus"""
    
    def __init__(self, prometheus_url: str = None):
        self.prometheus_url = prometheus_url or f"http://localhost:{settings.prometheus_port}"
        self.session = None
    
    async def _get_session(self):
        """Obtiene sesión HTTP reutilizable"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def collect_metrics(self, model_id: str) -> List[MetricData]:
        """Recolecta métricas desde Prometheus"""
        metrics = []
        
        try:
            # Queries de Prometheus para diferentes métricas
            queries = {
                MetricType.LATENCY: f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{model_id="{model_id}"}}[5m]))',
                MetricType.THROUGHPUT: f'rate(http_requests_total{{model_id="{model_id}"}}[5m])',
                MetricType.ERROR_RATE: f'rate(http_requests_total{{model_id="{model_id}", status=~"5.."}}) / rate(http_requests_total{{model_id="{model_id}"}})',
                MetricType.CPU_USAGE: f'cpu_usage_percent{{model_id="{model_id}"}}',
                MetricType.MEMORY_USAGE: f'memory_usage_bytes{{model_id="{model_id}"}} / 1024 / 1024'  # Convert to MB
            }
            
            session = await self._get_session()
            
            for metric_type, query in queries.items():
                try:
                    # Ejecutar query en Prometheus
                    async with session.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={"query": query}
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            # Procesar resultados
                            if data["status"] == "success" and data["data"]["result"]:
                                for result in data["data"]["result"]:
                                    timestamp = datetime.fromtimestamp(float(result["value"][0]))
                                    value = float(result["value"][1])
                                    
                                    # Crear métrica
                                    metric = MetricData(
                                        model_id=model_id,
                                        metric_type=metric_type.value,
                                        value=value,
                                        timestamp=timestamp,
                                        source="prometheus",
                                        tags=result.get("metric", {})
                                    )
                                    metrics.append(metric)
                        
                except Exception as e:
                    logger.warning(f"Error recolectando {metric_type} desde Prometheus: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error conectando a Prometheus: {e}")
        
        return metrics
    
    def get_source_name(self) -> str:
        return "prometheus"
    
    async def close(self):
        """Cierra la sesión HTTP"""
        if self.session:
            await self.session.close()


class ScaleAPIDataSource(DataSource):
    """Colector de métricas desde Scale AI API (simulado)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.scale_api_key
        self.base_url = settings.scale_api_url
        self.session = None
    
    async def _get_session(self):
        """Obtiene sesión HTTP con autenticación"""
        if self.session is None:
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def collect_metrics(self, model_id: str) -> List[MetricData]:
        """Recolecta métricas desde Scale AI API"""
        metrics = []
        
        if settings.mock_scale_api:
            # Datos simulados para desarrollo
            return self._generate_mock_metrics(model_id)
        
        try:
            session = await self._get_session()
            
            # Endpoints de Scale AI para métricas
            endpoints = {
                "model_performance": f"/models/{model_id}/performance",
                "usage_stats": f"/models/{model_id}/usage",
                "quality_metrics": f"/models/{model_id}/quality"
            }
            
            for endpoint_name, endpoint in endpoints.items():
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Procesar respuesta de Scale AI
                            parsed_metrics = self._parse_scale_response(
                                model_id, endpoint_name, data
                            )
                            metrics.extend(parsed_metrics)
                            
                except Exception as e:
                    logger.warning(f"Error recolectando desde {endpoint_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error conectando a Scale AI API: {e}")
            
        return metrics
    
    def _generate_mock_metrics(self, model_id: str) -> List[MetricData]:
        """Genera métricas simuladas para desarrollo"""
        timestamp = datetime.utcnow()
        
        # Simular algunas variaciones realistas
        base_accuracy = 0.892
        variation = np.random.normal(0, 0.02)  # Pequeña variación
        
        mock_metrics = [
            MetricData(
                model_id=model_id,
                metric_type=MetricType.ACCURACY.value,
                value=max(0.0, min(1.0, base_accuracy + variation)),
                timestamp=timestamp,
                source="scale_api",
                tags={"version": "1.2.3", "environment": "production"}
            ),
            MetricData(
                model_id=model_id,
                metric_type=MetricType.LATENCY.value,
                value=np.random.lognormal(3.8, 0.2),  # ~45ms promedio
                timestamp=timestamp,
                source="scale_api"
            ),
            MetricData(
                model_id=model_id,
                metric_type=MetricType.THROUGHPUT.value,
                value=np.random.normal(120, 15),  # ~120 RPS
                timestamp=timestamp,
                source="scale_api"
            )
        ]
        
        return mock_metrics
    
    def _parse_scale_response(
        self, 
        model_id: str, 
        endpoint_name: str, 
        data: Dict[str, Any]
    ) -> List[MetricData]:
        """Parsea respuesta de Scale AI API"""
        metrics = []
        timestamp = datetime.utcnow()
        
        # Mapeo específico de Scale AI
        if endpoint_name == "model_performance":
            if "accuracy" in data:
                metrics.append(MetricData(
                    model_id=model_id,
                    metric_type=MetricType.ACCURACY.value,
                    value=float(data["accuracy"]),
                    timestamp=timestamp,
                    source="scale_api"
                ))
        
        elif endpoint_name == "usage_stats":
            if "latency_p95" in data:
                metrics.append(MetricData(
                    model_id=model_id,
                    metric_type=MetricType.LATENCY.value,
                    value=float(data["latency_p95"]),
                    timestamp=timestamp,
                    source="scale_api"
                ))
        
        return metrics
    
    def get_source_name(self) -> str:
        return "scale_api"
    
    async def close(self):
        """Cierra la sesión HTTP"""
        if self.session:
            await self.session.close()


class CustomMetricsDataSource(DataSource):
    """Colector para métricas custom enviadas por webhook"""
    
    def __init__(self):
        self._metrics_buffer = {}  # Buffer temporal para métricas
    
    async def collect_metrics(self, model_id: str) -> List[MetricData]:
        """Recolecta métricas del buffer interno"""
        metrics = self._metrics_buffer.get(model_id, [])
        
        # Limpiar buffer después de recolectar
        if model_id in self._metrics_buffer:
            del self._metrics_buffer[model_id]
        
        return metrics
    
    def add_metric(self, metric: MetricData):
        """Añade una métrica al buffer"""
        if metric.model_id not in self._metrics_buffer:
            self._metrics_buffer[metric.model_id] = []
        
        self._metrics_buffer[metric.model_id].append(metric)
    
    def get_source_name(self) -> str:
        return "custom"


class MockDataSource(DataSource):
    """Colector de métricas simuladas para desarrollo"""
    
    def __init__(self):
        self.last_values = {}  # Para simular drift gradual
    
    async def collect_metrics(self, model_id: str) -> List[MetricData]:
        """Genera métricas simuladas realistas"""
        timestamp = datetime.utcnow()
        
        # Inicializar valores base si es la primera vez
        if model_id not in self.last_values:
            self.last_values[model_id] = {
                "accuracy": 0.892,
                "latency": 45.2,
                "throughput": 120.5,
                "error_rate": 0.002,
                "memory_usage": 1024.8,
                "cpu_usage": 68.5
            }
        
        # Simular drift gradual y variación natural
        values = self.last_values[model_id]
        
        # Accuracy: drift gradual hacia abajo
        accuracy_drift = np.random.normal(-0.0001, 0.005)  # Drift lento
        values["accuracy"] = max(0.7, min(1.0, values["accuracy"] + accuracy_drift))
        
        # Latency: variación normal con spikes ocasionales
        if np.random.random() < 0.05:  # 5% chance de spike
            latency_change = np.random.normal(20, 5)
        else:
            latency_change = np.random.normal(0, 2)
        values["latency"] = max(10, values["latency"] + latency_change)
        
        # Throughput: correlacionado negativamente con latency
        throughput_change = np.random.normal(0, 5) - (latency_change * 0.5)
        values["throughput"] = max(50, values["throughput"] + throughput_change)
        
        # Error rate: ocasionalmente sube
        if np.random.random() < 0.02:  # 2% chance de error spike
            error_change = np.random.exponential(0.01)
        else:
            error_change = np.random.normal(0, 0.0002)
        values["error_rate"] = max(0, min(0.1, values["error_rate"] + error_change))
        
        # Memory y CPU: variación normal
        values["memory_usage"] += np.random.normal(0, 50)
        values["cpu_usage"] += np.random.normal(0, 5)
        values["cpu_usage"] = max(10, min(100, values["cpu_usage"]))
        
        # Crear métricas
        metrics = [
            MetricData(
                model_id=model_id,
                metric_type=MetricType.ACCURACY.value,
                value=values["accuracy"],
                timestamp=timestamp,
                source="mock",
                tags={"version": "1.2.3", "environment": "production"}
            ),
            MetricData(
                model_id=model_id,
                metric_type=MetricType.LATENCY.value,
                value=values["latency"],
                timestamp=timestamp,
                source="mock"
            ),
            MetricData(
                model_id=model_id,
                metric_type=MetricType.THROUGHPUT.value,
                value=values["throughput"],
                timestamp=timestamp,
                source="mock"
            ),
            MetricData(
                model_id=model_id,
                metric_type=MetricType.ERROR_RATE.value,
                value=values["error_rate"],
                timestamp=timestamp,
                source="mock"
            ),
            MetricData(
                model_id=model_id,
                metric_type=MetricType.MEMORY_USAGE.value,
                value=values["memory_usage"],
                timestamp=timestamp,
                source="mock"
            ),
            MetricData(
                model_id=model_id,
                metric_type=MetricType.CPU_USAGE.value,
                value=values["cpu_usage"],
                timestamp=timestamp,
                source="mock"
            )
        ]
        
        return metrics
    
    def get_source_name(self) -> str:
        return "mock"


class DataCollectionEngine:
    """Motor principal de recolección de datos"""
    
    def __init__(self):
        self.data_sources = {}
        self.is_running = False
        self.collection_task = None
        
        # Inicializar fuentes de datos
        self._initialize_data_sources()
    
    def _initialize_data_sources(self):
        """Inicializa las fuentes de datos disponibles"""
        try:
            # Prometheus (si está disponible)
            self.data_sources["prometheus"] = PrometheusDataSource()
            logger.info("Prometheus data source initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Prometheus: {e}")
        
        try:
            # Scale AI API
            self.data_sources["scale_api"] = ScaleAPIDataSource()
            logger.info("Scale AI data source initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Scale AI API: {e}")
        
        # Custom metrics (siempre disponible)
        self.data_sources["custom"] = CustomMetricsDataSource()
        logger.info("Custom metrics data source initialized")
        
        # Mock data source (siempre disponible para desarrollo)
        self.data_sources["mock"] = MockDataSource()
        logger.info("Mock data source initialized")
    
    async def collect_model_metrics(self, model_id: str) -> List[MetricData]:
        """Recolecta métricas de todas las fuentes para un modelo"""
        all_metrics = []
        
        for source_name, data_source in self.data_sources.items():
            try:
                metrics = await data_source.collect_metrics(model_id)
                all_metrics.extend(metrics)
                logger.debug(f"Collected {len(metrics)} metrics from {source_name} for model {model_id}")
                
            except Exception as e:
                logger.error(f"Error collecting from {source_name} for model {model_id}: {e}")
                continue
        
        return all_metrics
    
    async def store_metrics(self, metrics: List[MetricData]):
        """Almacena métricas en la base de datos"""
        if not metrics:
            return
        
        try:
            with get_db_context() as db:
                for metric in metrics:
                    db_metric = ModelMetric(
                        model_id=metric.model_id,
                        metric_type=metric.metric_type,
                        value=metric.value,
                        timestamp=metric.timestamp,
                        source=metric.source,
                        tags=metric.tags
                    )
                    db.add(db_metric)
                
                logger.info(f"Stored {len(metrics)} metrics in database")
                
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
            raise
    
    async def start_continuous_collection(
        self, 
        model_ids: List[str], 
        interval_seconds: int = 60
    ):
        """Inicia recolección continua de métricas"""
        if self.is_running:
            logger.warning("Collection already running")
            return
        
        self.is_running = True
        self.collection_task = asyncio.create_task(
            self._collection_loop(model_ids, interval_seconds)
        )
        
        logger.info(f"Started continuous collection for {len(model_ids)} models, interval={interval_seconds}s")
    
    async def stop_continuous_collection(self):
        """Detiene la recolección continua"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        # Cerrar sesiones de fuentes de datos
        for data_source in self.data_sources.values():
            if hasattr(data_source, 'close'):
                await data_source.close()
        
        logger.info("Stopped continuous collection")
    
    async def _collection_loop(self, model_ids: List[str], interval_seconds: int):
        """Loop principal de recolección"""
        while self.is_running:
            try:
                start_time = datetime.utcnow()
                
                # Recolectar métricas para todos los modelos
                for model_id in model_ids:
                    try:
                        metrics = await self.collect_model_metrics(model_id)
                        await self.store_metrics(metrics)
                        
                    except Exception as e:
                        logger.error(f"Error processing model {model_id}: {e}")
                        continue
                
                # Calcular tiempo de sleep
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                sleep_time = max(0, interval_seconds - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"Collection took {elapsed:.2f}s, longer than interval {interval_seconds}s")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    def add_custom_metric(self, metric: MetricData):
        """Añade una métrica custom"""
        if "custom" in self.data_sources:
            self.data_sources["custom"].add_metric(metric)
    
    def get_available_sources(self) -> List[str]:
        """Retorna las fuentes de datos disponibles"""
        return list(self.data_sources.keys())


# Instancia global del motor de recolección
collection_engine = DataCollectionEngine() 
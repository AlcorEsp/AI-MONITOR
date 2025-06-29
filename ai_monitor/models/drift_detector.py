import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
from scipy import stats
from scipy.spatial.distance import jensenshannon
from sklearn.preprocessing import LabelEncoder
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


@dataclass
class DriftResult:
    """Resultado de detección de drift"""
    feature_name: str
    algorithm: str
    drift_score: float
    threshold: float
    is_drift_detected: bool
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    confidence: float = 0.95
    statistics: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DriftDetectionAlgorithm(ABC):
    """Base class para algoritmos de detección de drift"""
    
    @abstractmethod
    def detect_drift(
        self,
        reference_data: np.ndarray,
        current_data: np.ndarray,
        threshold: float = 0.05
    ) -> DriftResult:
        """Detecta drift entre dos datasets"""
        pass
    
    @abstractmethod
    def supports_feature_type(self, feature_type: str) -> bool:
        """Indica si el algoritmo soporta este tipo de feature"""
        pass


class KolmogorovSmirnovDrift(DriftDetectionAlgorithm):
    """Kolmogorov-Smirnov test para detección de drift en features numéricas"""
    
    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        self.name = "ks_test"
    
    def detect_drift(
        self,
        reference_data: np.ndarray,
        current_data: np.ndarray,
        threshold: float = 0.05
    ) -> DriftResult:
        """
        KS test compara las distribuciones de dos muestras
        H0: Las muestras provienen de la misma distribución
        """
        try:
            # Limpiar datos
            ref_clean = reference_data[~np.isnan(reference_data)]
            cur_clean = current_data[~np.isnan(current_data)]
            
            if len(ref_clean) == 0 or len(cur_clean) == 0:
                raise ValueError("Datos insuficientes después de limpieza")
            
            # Ejecutar KS test
            ks_statistic, p_value = stats.ks_2samp(ref_clean, cur_clean)
            
            # Calcular effect size (Cohen's d aproximado)
            pooled_std = np.sqrt(((np.std(ref_clean) ** 2) + (np.std(cur_clean) ** 2)) / 2)
            effect_size = abs(np.mean(ref_clean) - np.mean(cur_clean)) / pooled_std if pooled_std > 0 else 0
            
            is_drift = p_value < threshold
            
            statistics = {
                "ks_statistic": float(ks_statistic),
                "p_value": float(p_value),
                "effect_size": float(effect_size),
                "reference_mean": float(np.mean(ref_clean)),
                "current_mean": float(np.mean(cur_clean)),
                "reference_std": float(np.std(ref_clean)),
                "current_std": float(np.std(cur_clean)),
                "reference_size": len(ref_clean),
                "current_size": len(cur_clean)
            }
            
            return DriftResult(
                feature_name=self.feature_name,
                algorithm=self.name,
                drift_score=float(ks_statistic),
                threshold=threshold,
                is_drift_detected=is_drift,
                p_value=float(p_value),
                effect_size=float(effect_size),
                statistics=statistics
            )
            
        except Exception as e:
            logger.error(f"Error en KS test para {self.feature_name}: {e}")
            raise
    
    def supports_feature_type(self, feature_type: str) -> bool:
        return feature_type in ["numerical", "continuous"]


class DriftDetectionEngine:
    """Motor principal de detección de drift"""
    
    def __init__(self):
        self.algorithms = {
            "ks_test": KolmogorovSmirnovDrift
        }
    
    def detect_feature_drift(
        self,
        feature_name: str,
        reference_data: Union[np.ndarray, pd.Series, List],
        current_data: Union[np.ndarray, pd.Series, List],
        feature_type: str = "numerical",
        algorithm: str = "ks_test",
        threshold: float = 0.05
    ) -> DriftResult:
        """Detecta drift en una feature específica"""
        # Convertir a numpy arrays
        ref_array = np.array(reference_data, dtype=float)
        cur_array = np.array(current_data, dtype=float)
        
        # Crear instancia del algoritmo
        algo_class = self.algorithms[algorithm]
        detector = algo_class(feature_name)
        
        # Detectar drift
        result = detector.detect_drift(ref_array, cur_array, threshold)
        
        logger.info(f"Drift detection completada para {feature_name}: "
                   f"algoritmo={algorithm}, drift_detected={result.is_drift_detected}, "
                   f"score={result.drift_score:.4f}")
        
        return result 
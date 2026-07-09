from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats


class PriorAnalyzer:

    def __init__(self):
        pass

    @staticmethod
    def get_scale_from_data(data: np.ndarray, method: str = "mad") -> float:
        if len(data) < 2:
            return 1.0
        
        if method == "mad":
            median = np.median(data)
            mad = np.median(np.abs(data - median))
            return mad / 0.6745 if mad > 0 else 1.0
        else:
            return float(np.std(data)) or 1.0

    @staticmethod
    def analyze_distribution(
        data: np.ndarray, 
        allow_negative: bool = True,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        data = np.asarray(data).flatten()
        if len(data) < 3:
            return {
                "skewness": 0.0,
                "kurtosis": 0.0,
                "outlier_ratio": 0.0,
                "shapiro_stat": None,
                "shapiro_pvalue": None,
                "anderson_stat": None,
                "anderson_crit": None,
                "is_normal": True,
                "is_exponential": False,
                "is_heavy_tailed": False,
                "data_min": float(np.min(data)),
                "data_max": float(np.max(data)),
            }

        skewness = float(stats.skew(data))
        kurtosis = float(stats.kurtosis(data))  # excess kurtosis
        mean = np.mean(data)
        std = np.std(data)
        outlier_ratio = float(np.sum(np.abs(data - mean) > 3 * std) / len(data)) if std > 0 else 0.0
        shapiro_stat = None
        shapiro_pvalue = None
        is_normal = False
        
        if len(data) >= 3 and len(data) <= 5000:
            try:
                shapiro_stat, shapiro_pvalue = stats.shapiro(data)
                is_normal = shapiro_pvalue > alpha
            except Exception:
                pass
        
        anderson_stat = None
        anderson_crit = None
        is_exponential = False
        
        if allow_negative is False or np.all(data > 0):
            try:
                if len(data) > 1:
                    data_min = np.min(data)
                    data_range = np.max(data) - data_min
                    if data_range > 0:
                        data_norm = (data - data_min) / data_range
                        result = stats.anderson(data_norm, dist='expon')
                        anderson_stat = float(result.statistic)
                        anderson_crit = float(result.critical_values[2])  # 5% level
                        is_exponential = anderson_stat < anderson_crit
            except Exception:
                pass
        
        is_heavy_tailed = kurtosis > 3.0
        
        return {
            "skewness": skewness,
            "kurtosis": kurtosis,
            "outlier_ratio": outlier_ratio,
            "shapiro_stat": shapiro_stat,
            "shapiro_pvalue": shapiro_pvalue,
            "anderson_stat": anderson_stat,
            "anderson_crit": anderson_crit,
            "is_normal": is_normal,
            "is_exponential": is_exponential,
            "is_heavy_tailed": is_heavy_tailed,
            "data_min": float(np.min(data)),
            "data_max": float(np.max(data)),
        }

    @staticmethod
    def recommend_prior_family(
        analysis: Dict[str, Any],
        is_positive_constrained: bool = False,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        skewness = analysis["skewness"]
        kurtosis = analysis["kurtosis"]
        outlier_ratio = analysis["outlier_ratio"]
        is_normal = analysis["is_normal"]
        is_exponential = analysis["is_exponential"]
        is_heavy_tailed = analysis["is_heavy_tailed"]
        
        if is_heavy_tailed and (outlier_ratio > 0.01 or kurtosis > 5):
            return {
                "family": "HalfStudentT" if is_positive_constrained else "StudentT",
                "reasoning": f"Heavy-tailed distribution (kurtosis={kurtosis:.2f}, outliers={outlier_ratio*100:.1f}%)",
                "confidence": 0.85,
                "nu": 3,
            }
        
        if is_positive_constrained and skewness > 1.0:
            if is_exponential:
                return {
                    "family": "Exponential",
                    "reasoning": f"Right-skewed exponential distribution (skewness={skewness:.2f}, Anderson-Darling test)",
                    "confidence": 0.90,
                }
            else:
                return {
                    "family": "Gamma",
                    "reasoning": f"Right-skewed distribution (skewness={skewness:.2f}), Gamma more flexible than Exponential",
                    "confidence": 0.80,
                }
        
        if is_positive_constrained and 0.3 < skewness <= 1.0:
            if outlier_ratio > 0.005:
                return {
                    "family": "Exponential",
                    "reasoning": f"Moderate right-skew with outliers (skewness={skewness:.2f}), Exponential more robust",
                    "confidence": 0.75,
                }
            else:
                return {
                    "family": "HalfNormal",
                    "reasoning": f"Moderate right-skew, clean data (skewness={skewness:.2f})",
                    "confidence": 0.70,
                }

        if is_normal or abs(skewness) < 0.5:
            if is_positive_constrained:
                return {
                    "family": "HalfNormal",
                    "reasoning": f"Approximately normal/symmetric, positive-constrained (skewness={skewness:.2f})",
                    "confidence": 0.85,
                }
            else:
                return {
                    "family": "Normal",
                    "reasoning": f"Approximately normal distribution (Shapiro-Wilk test or skewness={skewness:.2f})",
                    "confidence": 0.85,
                }
        
        if is_positive_constrained:
            return {
                "family": "HalfNormal",
                "reasoning": "Default weakly informative prior for positive-constrained parameter",
                "confidence": 0.60,
            }
        else:
            return {
                "family": "Normal",
                "reasoning": "Default weakly informative prior",
                "confidence": 0.60,
            }

    @staticmethod
    def extract_prior_from_checkpoint(
        checkpoint: Dict[str, Any],
        metric_type: str = "price"
    ) -> Dict[str, Any]:
        posterior_key = f"{metric_type}_posteriors"
        
        if posterior_key not in checkpoint:
            return None
        
        posteriors = np.array(checkpoint[posterior_key])
        
        posteriors_flat = posteriors.flatten()
        
        return {
            "mu": float(np.mean(posteriors_flat)),
            "sigma": float(np.std(posteriors_flat)),
            "sample_mean": float(np.mean(posteriors_flat)),
            "sample_std": float(np.std(posteriors_flat)),
            "n_samples": len(posteriors_flat),
        }

    @staticmethod
    def get_hierarchical_analysis(
        metric_values: np.ndarray,
        item_codes: np.ndarray,
        vendor_codes: np.ndarray,
    ) -> Dict[str, Dict[str, Any]]:
        analysis = {}
        
        analysis["transaction"] = PriorAnalyzer.analyze_distribution(
            metric_values, 
            allow_negative=True
        )
        
        item_means = np.array([
            np.mean(metric_values[item_codes == i]) 
            for i in np.unique(item_codes)
        ])
        analysis["item"] = PriorAnalyzer.analyze_distribution(
            item_means,
            allow_negative=True
        )
        
        vendor_means = np.array([
            np.mean(metric_values[vendor_codes == i]) 
            for i in np.unique(vendor_codes)
        ])
        analysis["vendor"] = PriorAnalyzer.analyze_distribution(
            vendor_means,
            allow_negative=True
        )
        
        return analysis

"""
Prior analyzer for Bayesian Hierarchical Model.
Automatically detects data distributions and recommends optimal prior families.
Supports Bayesian updating with posterior checkpoints from previous years.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats


class PriorAnalyzer:
    """
    Analyzes data distributions and recommends appropriate prior families for BHM models.
    
    Supports prior families: Normal, Exponential, Gamma, HalfNormal, HalfStudentT
    Uses hybrid approach: heuristics (skewness/kurtosis) + statistical tests (Shapiro-Wilk, Anderson-Darling)
    """

    def __init__(self):
        pass

    @staticmethod
    def get_scale_from_data(data: np.ndarray, method: str = "mad") -> float:
        """
        Extract robust scale estimate from data.
        
        Args:
            data: 1D array of observations
            method: 'mad' (median absolute deviation) or 'std' (standard deviation)
        
        Returns:
            Robust scale estimate
        """
        if len(data) < 2:
            return 1.0
        
        if method == "mad":
            # Median Absolute Deviation (robust to outliers)
            median = np.median(data)
            mad = np.median(np.abs(data - median))
            # Scale MAD to match standard deviation for normal data
            return mad / 0.6745 if mad > 0 else 1.0
        else:
            return float(np.std(data)) or 1.0

    @staticmethod
    def analyze_distribution(
        data: np.ndarray, 
        allow_negative: bool = True,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Analyze distributional properties of data using heuristics + statistical tests.
        
        Args:
            data: 1D array of observations
            allow_negative: Whether data can take negative values
            alpha: Significance level for statistical tests
        
        Returns:
            Dictionary with analysis results:
            - skewness: Fisher-Pearson skewness coefficient
            - kurtosis: Fisher's definition (excess kurtosis)
            - outlier_ratio: Proportion of points >3σ from mean
            - shapiro_stat: Shapiro-Wilk test statistic for normality
            - shapiro_pvalue: p-value for Shapiro-Wilk test
            - anderson_stat: Anderson-Darling test statistic
            - anderson_crit: Anderson-Darling critical value
            - is_normal: Boolean, likely normally distributed
            - is_exponential: Boolean, likely exponentially distributed (if positive)
            - is_heavy_tailed: Boolean, heavy-tailed (high kurtosis)
        """
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

        # Heuristic 1: Skewness and Kurtosis
        skewness = float(stats.skew(data))
        kurtosis = float(stats.kurtosis(data))  # excess kurtosis
        
        # Heuristic 2: Outlier ratio
        mean = np.mean(data)
        std = np.std(data)
        outlier_ratio = float(np.sum(np.abs(data - mean) > 3 * std) / len(data)) if std > 0 else 0.0
        
        # Statistical Test 1: Shapiro-Wilk for normality
        shapiro_stat = None
        shapiro_pvalue = None
        is_normal = False
        
        if len(data) >= 3 and len(data) <= 5000:
            try:
                shapiro_stat, shapiro_pvalue = stats.shapiro(data)
                is_normal = shapiro_pvalue > alpha
            except Exception:
                pass
        
        # Statistical Test 2: Anderson-Darling for exponentiality (if data is positive)
        anderson_stat = None
        anderson_crit = None
        is_exponential = False
        
        if allow_negative is False or np.all(data > 0):
            try:
                # Normalize to [0,1] for Anderson-Darling
                if len(data) > 1:
                    data_min = np.min(data)
                    data_range = np.max(data) - data_min
                    if data_range > 0:
                        data_norm = (data - data_min) / data_range
                        # Fit exponential and test
                        result = stats.anderson(data_norm, dist='expon')
                        anderson_stat = float(result.statistic)
                        anderson_crit = float(result.critical_values[2])  # 5% level
                        is_exponential = anderson_stat < anderson_crit
            except Exception:
                pass
        
        # Heavy tails detection
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
        """
        Recommend prior family based on data analysis.
        
        Args:
            analysis: Output from analyze_distribution()
            is_positive_constrained: Whether parameter must be positive (scale params)
            confidence_threshold: Threshold for statistical test evidence
        
        Returns:
            Dictionary with:
            - family: Recommended prior family (str)
            - reasoning: Explanation of recommendation
            - confidence: Confidence score [0, 1]
        """
        skewness = analysis["skewness"]
        kurtosis = analysis["kurtosis"]
        outlier_ratio = analysis["outlier_ratio"]
        is_normal = analysis["is_normal"]
        is_exponential = analysis["is_exponential"]
        is_heavy_tailed = analysis["is_heavy_tailed"]
        
        # Decision tree
        
        # Rule 1: Heavy tails → HalfStudentT (robust to outliers)
        if is_heavy_tailed and (outlier_ratio > 0.01 or kurtosis > 5):
            return {
                "family": "HalfStudentT" if is_positive_constrained else "StudentT",
                "reasoning": f"Heavy-tailed distribution (kurtosis={kurtosis:.2f}, outliers={outlier_ratio*100:.1f}%)",
                "confidence": 0.85,
                "nu": 3,  # degrees of freedom for heavy tails
            }
        
        # Rule 2: Highly right-skewed & positive constrained → Exponential or Gamma
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
        
        # Rule 3: Moderately right-skewed & positive constrained → HalfNormal or Exponential
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
        
        # Rule 4: Near-normal or symmetric → Normal or HalfNormal (if positive constrained)
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
        
        # Default fallback
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
        """
        Extract prior hyperparameters from previous year's posterior checkpoint.
        
        Args:
            checkpoint: Dictionary with posteriors from previous year
                Expected keys: 'price_posteriors' or 'timeliness_posteriors'
            metric_type: 'price' or 'timeliness'
        
        Returns:
            Dictionary with:
            - mu: Mean of previous year's posterior (for hyperprior)
            - sigma: Std of previous year's posterior (for hyperprior)
            - sample_mean: Mean of posterior samples
            - sample_std: Std of posterior samples
        """
        posterior_key = f"{metric_type}_posteriors"
        
        if posterior_key not in checkpoint:
            return None
        
        posteriors = np.array(checkpoint[posterior_key])
        
        # Flatten if multi-chain
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
        """
        Analyze data at different hierarchical levels.
        
        Args:
            metric_values: 1D array of metric values
            item_codes: Item category codes for each observation
            vendor_codes: Vendor category codes for each observation
        
        Returns:
            Dictionary with analysis for each level:
            {
                'transaction': {...analysis for raw data...},
                'item': {...analysis for item-level residuals...},
                'vendor': {...analysis for vendor-level residuals...}
            }
        """
        analysis = {}
        
        # Transaction-level (raw data)
        analysis["transaction"] = PriorAnalyzer.analyze_distribution(
            metric_values, 
            allow_negative=True
        )
        
        # Item-level: compute item means and analyze variance
        item_means = np.array([
            np.mean(metric_values[item_codes == i]) 
            for i in np.unique(item_codes)
        ])
        analysis["item"] = PriorAnalyzer.analyze_distribution(
            item_means,
            allow_negative=True
        )
        
        # Vendor-level: compute vendor means
        vendor_means = np.array([
            np.mean(metric_values[vendor_codes == i]) 
            for i in np.unique(vendor_codes)
        ])
        analysis["vendor"] = PriorAnalyzer.analyze_distribution(
            vendor_means,
            allow_negative=True
        )
        
        return analysis

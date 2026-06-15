"""
Bayesian Hierarchical Model service for vendor performance assessment.
Supports adaptive priors based on data distribution analysis.
Supports Bayesian updating using posteriors from previous years.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import hashlib

try:
    import pymc as pm
    import arviz as az
except ImportError:
    pm = None
    az = None

from src.types.models import VendorBHMScore, BHMRankingsResponse, BHMDiagnostics
from src.services.prior_analyzer import PriorAnalyzer
from src.services.mcmc_diagnostics import MCMCDiagnostics


class BHMService:
    """
    Bayesian Hierarchical Model for vendor ranking.
    
    Supports:
    - Data-driven adaptive priors
    - Hierarchical analysis (transaction, item, vendor levels)
    - Bayesian updating from previous year posteriors
    - Full prior analysis audit trail
    """

    def __init__(
        self, 
        mcmc_iterations: int = 8000, 
        mcmc_chains: int = 8, 
        mcmc_tuning: int = 2000
    ):
        """Initialize BHM service with MCMC configuration."""
        if pm is None:
            raise ImportError(
                "PyMC is required for BHM functionality. "
                "Install with: pip install pymc arviz"
            )

        self.mcmc_iterations = mcmc_iterations
        self.mcmc_chains = mcmc_chains
        self.mcmc_tuning = mcmc_tuning

        self.price_model = None
        self.timeliness_model = None
        self.price_idata = None
        self.timeliness_idata = None

        # Vendor/item ID maps from model fitting (Categorical-sorted order)
        self.price_vendor_id_map: Dict[int, str] = {}
        self.timeliness_vendor_id_map: Dict[int, str] = {}

        # Data standardization parameters
        self.price_data_mean = 0.0
        self.price_data_std = 1.0
        self.timeliness_data_mean = 0.0
        self.timeliness_data_std = 1.0
        
        self.prior_analyzer = PriorAnalyzer()
        self.prior_analysis_log: Dict[str, Dict[str, Any]] = {}

    def _hash_data(self, df: pd.DataFrame, metric_column: str) -> str:
        """Create hash of data to detect if analysis cache is valid."""
        key_cols = [metric_column, "product_code", "vendor_name"]
        available = [c for c in key_cols if c in df.columns]
        data_bytes = pd.util.hash_pandas_object(
            df[available], index=True
        ).values.tobytes()
        return hashlib.md5(data_bytes).hexdigest()


    def prepare_hierarchical_data(
        self,
        df: pd.DataFrame,
        metric_column: str,
        item_column: str = "product_code",
        vendor_column: str = "vendor_name",
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[int, str], Dict[int, str]]:

        actual_metric_col = metric_column
        if metric_column == "delay" and "delay_days" in df.columns:
            actual_metric_col = "delay_days"
        
        available_cols = df.columns.tolist()
        required_cols = [actual_metric_col, item_column, vendor_column]
        missing_cols = [col for col in required_cols if col not in available_cols]
        
        if missing_cols:
            raise ValueError(
                f"Missing required columns for {metric_column}: {missing_cols}. "
                f"Available columns: {available_cols}"
            )
        
        try:
            # Only drop NaNs in the metric and vendor columns (not product_code)
            # This preserves transactions with missing product codes
            df_clean = df[[actual_metric_col, item_column, vendor_column]].copy()
            df_clean = df_clean.dropna(subset=[actual_metric_col, vendor_column])
        except Exception as e:
            raise ValueError(f"Error selecting columns {required_cols}: {str(e)}")

        if len(df_clean) == 0:
            raise ValueError(f"No valid data for {metric_column} metric after removing NaN values")

        item_codes = pd.Categorical(df_clean[item_column]).codes
        vendor_codes = pd.Categorical(df_clean[vendor_column]).codes

        item_id_map = dict(enumerate(pd.Categorical(df_clean[item_column]).categories))
        vendor_id_map = dict(enumerate(pd.Categorical(df_clean[vendor_column]).categories))

        metric_values = df_clean[actual_metric_col].values.astype(float)

        return metric_values, item_codes, vendor_codes, item_id_map, vendor_id_map

    def _analyze_and_recommend_priors(
        self,
        metric_values: np.ndarray,
        item_codes: np.ndarray,
        vendor_codes: np.ndarray,
        metric_type: str,
        prior_checkpoint: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze data distribution and recommend priors.
        Returns prior specifications for model construction.
        """
        analysis = self.prior_analyzer.get_hierarchical_analysis(
            metric_values, item_codes, vendor_codes
        )
        
        priors = {}
        
        # Transaction-level scale (for all sigma parameters)
        scale_transaction = self.prior_analyzer.get_scale_from_data(metric_values)
        
        # Recommend vendor-level priors
        vendor_rec = self.prior_analyzer.recommend_prior_family(
            analysis["vendor"],
            is_positive_constrained=True
        )
        
        # Recommend item-level priors
        item_rec = self.prior_analyzer.recommend_prior_family(
            analysis["item"],
            is_positive_constrained=True
        )
        
        # Recommend transaction-level noise prior
        transaction_rec = self.prior_analyzer.recommend_prior_family(
            analysis["transaction"],
            is_positive_constrained=True
        )
        
        # Store analysis log
        self.prior_analysis_log[metric_type] = {
            "analysis": {
                "transaction": analysis["transaction"],
                "item": analysis["item"],
                "vendor": analysis["vendor"],
            },
            "recommendations": {
                "vendor": vendor_rec,
                "item": item_rec,
                "transaction": transaction_rec,
            },
            "scale_transaction": scale_transaction,
            "timestamp": datetime.utcnow().isoformat(),
            "using_checkpoint": prior_checkpoint is not None,
        }
        
        # Log prior recommendations for debugging
        print(f"\n[Prior Analysis - {metric_type}]")
        print(f"  Transaction scale: {scale_transaction:.4f}")
        print(f"  Vendor prior family: {vendor_rec['family']} (confidence: {vendor_rec.get('confidence', 'N/A')})")
        print(f"  Item prior family: {item_rec['family']} (confidence: {item_rec.get('confidence', 'N/A')})")
        print(f"  Transaction prior family: {transaction_rec['family']} (confidence: {transaction_rec.get('confidence', 'N/A')})")
        print(f"  Scale factor applied: 0.7 (70% regularization)")
        print(f"  Using checkpoint: {prior_checkpoint is not None}")
        
        # Handle Bayesian updating if checkpoint provided
        if prior_checkpoint:
            checkpoint_prior = self.prior_analyzer.extract_prior_from_checkpoint(
                prior_checkpoint, 
                metric_type=metric_type
            )
            if checkpoint_prior:
                priors["vendor_mu_prior"] = checkpoint_prior["mu"]
                priors["vendor_sigma_prior"] = checkpoint_prior["sigma"]
        
        # Prior regularization for sparse data
        # (Reduces divergences without over-constraining the posterior)
        scale_factor = 0.7  # Use 70% of original scales (less aggressive)
        
        priors.update({
            "vendor_rec": vendor_rec,
            "item_rec": item_rec,
            "transaction_rec": transaction_rec,
            "scale_transaction": scale_transaction * scale_factor,  # Regularized scale
            "scale_factor": scale_factor,
        })
        
        return priors


    def fit_price_model(
        self, 
        df: pd.DataFrame, 
        prior_checkpoint: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Fit hierarchical model for price_discrepancy.
        
        3-level hierarchy:
        - Level 1: Within-item variation (transaction-level noise)
        - Level 2: Between-item variation (item-level effects)
        - Level 3: Between-vendor variation (vendor-level effects)
        """
        try:
            metric_values, item_codes, vendor_codes, item_map, vendor_map = (
                self.prepare_hierarchical_data(df, "price_discrepancy")
            )

            n_items = len(item_map)
            n_vendors = len(vendor_map)
            
            # Standardize data for better MCMC convergence
            metric_mean = np.mean(metric_values)
            metric_std = np.std(metric_values)
            metric_std = metric_std if metric_std > 0 else 1.0
            metric_values_std = (metric_values - metric_mean) / metric_std
            
            # Get adaptive priors
            priors = self._analyze_and_recommend_priors(
                metric_values_std, item_codes, vendor_codes,
                metric_type="price",
                prior_checkpoint=prior_checkpoint,
            )
            
            # Store standardization parameters for later predictions
            self.price_data_mean = metric_mean
            self.price_data_std = metric_std
            self.price_vendor_id_map = vendor_map

            with pm.Model() as model:
                # Vendor-level hyperpriors
                if "vendor_mu_prior" in priors:
                    # Use checkpoint-based prior (Bayesian updating)
                    vendor_mu = pm.Normal(
                        "vendor_mu",
                        mu=priors["vendor_mu_prior"],
                        sigma=priors["vendor_sigma_prior"]
                    )
                else:
                    # Default weakly informative
                    vendor_mu = pm.Normal("vendor_mu", mu=0, sigma=priors["scale_transaction"] * 10)
                
                vendor_sigma = self._construct_prior(
                    "vendor_sigma",
                    priors["vendor_rec"],
                    scale=priors["scale_transaction"]
                )

                # Non-centered parameterization for vendor effects
                vendor_effects_raw = pm.Normal("vendor_effects_raw", mu=0, sigma=1, shape=n_vendors)
                vendor_effects = pm.Deterministic(
                    "vendor_effects",
                    vendor_mu + vendor_sigma * vendor_effects_raw
                )
                
                # Item-level hyperpriors
                item_mu = pm.Normal("item_mu", mu=0, sigma=priors["scale_transaction"] * 5)
                item_sigma = self._construct_prior(
                    "item_sigma",
                    priors["item_rec"],
                    scale=priors["scale_transaction"] * 0.5
                )

                # Non-centered parameterization for item effects
                item_effects_raw = pm.Normal("item_effects_raw", mu=0, sigma=1, shape=n_items)
                item_effects = pm.Deterministic(
                    "item_effects",
                    item_mu + item_sigma * item_effects_raw
                )

                # Transaction-level noise
                sigma_transaction = self._construct_prior(
                    "sigma_transaction",
                    priors["transaction_rec"],
                    scale=priors["scale_transaction"]
                )

                mu = vendor_effects[vendor_codes] + item_effects[item_codes]

                y = pm.Normal(
                    "y",
                    mu=mu,
                    sigma=sigma_transaction,
                    observed=metric_values_std,
                )

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.price_idata = pm.sample(
                        draws=self.mcmc_iterations,
                        tune=self.mcmc_tuning,
                        chains=self.mcmc_chains,
                        return_inferencedata=True,
                        progressbar=False,
                        random_seed=42,
                        target_accept=0.95,  # Higher target_accept for better adaptation
                    )

            self.price_model = model
            return True

        except Exception as e:
            print(f"Error fitting price model: {e}")
            return False


    def fit_timeliness_model(
        self, 
        df: pd.DataFrame, 
        prior_checkpoint: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Fit hierarchical model for delay (timeliness).
        Uses adaptive priors based on data distribution analysis.
        """
        try:
            metric_values, item_codes, vendor_codes, item_map, vendor_map = (
                self.prepare_hierarchical_data(df, "delay")
            )

            n_items = len(item_map)
            n_vendors = len(vendor_map)
            
            # Standardize data for better MCMC convergence
            metric_mean = np.mean(metric_values)
            metric_std = np.std(metric_values)
            metric_std = metric_std if metric_std > 0 else 1.0
            metric_values_std = (metric_values - metric_mean) / metric_std
            
            # Get adaptive priors
            priors = self._analyze_and_recommend_priors(
                metric_values_std, item_codes, vendor_codes,
                metric_type="timeliness",
                prior_checkpoint=prior_checkpoint,
            )
            
            # Store standardization parameters for later predictions
            self.timeliness_data_mean = metric_mean
            self.timeliness_data_std = metric_std
            self.timeliness_vendor_id_map = vendor_map

            with pm.Model() as model:
                # Vendor-level hyperpriors
                if "vendor_mu_prior" in priors:
                    # Use checkpoint-based prior (Bayesian updating)
                    vendor_mu = pm.Normal(
                        "vendor_mu",
                        mu=priors["vendor_mu_prior"],
                        sigma=priors["vendor_sigma_prior"]
                    )
                else:
                    # Default weakly informative
                    vendor_mu = pm.Normal("vendor_mu", mu=0, sigma=priors["scale_transaction"] * 2)
                
                vendor_sigma = self._construct_prior(
                    "vendor_sigma",
                    priors["vendor_rec"],
                    scale=priors["scale_transaction"]
                )

                # Non-centered parameterization for vendor effects
                vendor_effects_raw = pm.Normal("vendor_effects_raw", mu=0, sigma=1, shape=n_vendors)
                vendor_effects = pm.Deterministic(
                    "vendor_effects",
                    vendor_mu + vendor_sigma * vendor_effects_raw
                )

                # Item-level hyperpriors
                item_mu = pm.Normal("item_mu", mu=0, sigma=priors["scale_transaction"])
                item_sigma = self._construct_prior(
                    "item_sigma",
                    priors["item_rec"],
                    scale=priors["scale_transaction"] * 0.5
                )

                # Non-centered parameterization for item effects
                item_effects_raw = pm.Normal("item_effects_raw", mu=0, sigma=1, shape=n_items)
                item_effects = pm.Deterministic(
                    "item_effects",
                    item_mu + item_sigma * item_effects_raw
                )

                # Transaction-level noise
                sigma_transaction = self._construct_prior(
                    "sigma_transaction",
                    priors["transaction_rec"],
                    scale=priors["scale_transaction"]
                )

                mu = vendor_effects[vendor_codes] + item_effects[item_codes]

                y = pm.Normal(
                    "y",
                    mu=mu,
                    sigma=sigma_transaction,
                    observed=metric_values_std,
                )

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.timeliness_idata = pm.sample(
                        draws=self.mcmc_iterations,
                        tune=self.mcmc_tuning,
                        chains=self.mcmc_chains,
                        return_inferencedata=True,
                        progressbar=False,
                        random_seed=42,
                        target_accept=0.95,  # Higher target_accept for better adaptation
                    )

            self.timeliness_model = model
            return True

        except Exception as e:
            print(f"Error fitting timeliness model: {e}")
            return False

    @staticmethod
    def _construct_prior(name: str, recommendation: Dict[str, Any], scale: float):
        """Construct PyMC prior distribution based on recommendation."""
        family = recommendation["family"]
        
        if family == "Normal":
            return pm.Normal(name, mu=0, sigma=scale)
        elif family == "HalfNormal":
            return pm.HalfNormal(name, sigma=scale)
        elif family == "Exponential":
            lam = 1.0 / scale if scale > 0 else 1.0
            return pm.Exponential(name, lam=lam)
        elif family == "Gamma":
            # Shape=2, scale=scale (mean = 2*scale)
            return pm.Gamma(name, alpha=2, beta=1.0/scale)
        elif family == "HalfStudentT":
            nu = recommendation.get("nu", 3)
            return pm.HalfStudentT(name, nu=nu, sigma=scale)
        else:
            # Fallback
            return pm.HalfNormal(name, sigma=scale)


    def check_convergence(self) -> Tuple[str, List[str]]:

        warnings_list = []
        convergence_status = "converged"

        if self.price_idata is not None:
            price_rhat = az.rhat(self.price_idata)
            price_max_rhat = float(max(
                [v.max().values for v in price_rhat.data_vars.values() if v.max().values is not None]
            ))

            if price_max_rhat > 1.01:
                warnings_list.append(f"Price model: max Rhat = {price_max_rhat:.3f} (warning)")
                convergence_status = "not_converged"

        if self.timeliness_idata is not None:
            timeliness_rhat = az.rhat(self.timeliness_idata)
            timeliness_max_rhat = float(max(
                [v.max().values for v in timeliness_rhat.data_vars.values() if v.max().values is not None]
            ))

            if timeliness_max_rhat > 1.01:
                warnings_list.append(f"Timeliness model: max Rhat = {timeliness_max_rhat:.3f} (warning)")
                convergence_status = "not_converged"

        return convergence_status, warnings_list

    def get_diagnostics(self) -> List[BHMDiagnostics]:
        """Get MCMC convergence diagnostics for all model parameters."""
        diagnostics = []

        if self.price_idata is not None:
            price_rhat = az.rhat(self.price_idata)
            for var_name, var_data in price_rhat.data_vars.items():
                max_rhat = float(var_data.max().values)
                diagnostics.append(BHMDiagnostics(
                    metric_name=f"price_discrepancy_{var_name}",
                    r_hat=max_rhat,
                    effective_sample_size=0,
                    has_divergences=False,
                    rhat_status="good" if max_rhat < 1.01 else "warning",
                ))

        if self.timeliness_idata is not None:
            timeliness_rhat = az.rhat(self.timeliness_idata)
            for var_name, var_data in timeliness_rhat.data_vars.items():
                max_rhat = float(var_data.max().values)
                diagnostics.append(BHMDiagnostics(
                    metric_name=f"timeliness_{var_name}",
                    r_hat=max_rhat,
                    effective_sample_size=0,
                    has_divergences=False,
                    rhat_status="good" if max_rhat < 1.01 else "warning",
                ))

        return diagnostics


    def compute_vendor_scores(self, df: pd.DataFrame) -> List[VendorBHMScore]:
        """Compute vendor scores from posterior distributions."""
        import traceback
        print("[COMPUTE_SCORES] Starting", flush=True)
        try:
            if self.price_idata is None or self.timeliness_idata is None:
                print("[COMPUTE_SCORES] ERROR: Missing idata", flush=True)
                return []

            if not self.price_vendor_id_map or not self.timeliness_vendor_id_map:
                print("[COMPUTE_SCORES] ERROR: Vendor ID maps not populated", flush=True)
                return []

            # Clean data to match what was used in model fitting
            delay_col = "delay_days" if "delay_days" in df.columns else "delay"
            df_clean = df.dropna(subset=["vendor_name", "price_discrepancy", delay_col])

            vendor_names = df_clean["vendor_name"].unique()
            print(f"[COMPUTE_SCORES] Found {len(vendor_names)} vendors", flush=True)

            # Build reverse map: vendor_name -> model index (Categorical-sorted order)
            price_name_to_idx = {name: idx for idx, name in self.price_vendor_id_map.items()}
            timeliness_name_to_idx = {name: idx for idx, name in self.timeliness_vendor_id_map.items()}

            # Get full posterior arrays: shape (chains, draws, n_vendors)
            price_posterior_all = self.price_idata.posterior["vendor_effects"].values
            timeliness_posterior_all = self.timeliness_idata.posterior["vendor_effects"].values

            print(f"[COMPUTE_SCORES] Price posterior shape: {price_posterior_all.shape}", flush=True)
            print(f"[COMPUTE_SCORES] Timeliness posterior shape: {timeliness_posterior_all.shape}", flush=True)

            def extract_vendor_id(vendor_name):
                """Extract numeric vendor ID from vendor name."""
                if pd.isna(vendor_name):
                    return None
                name_str = str(vendor_name).strip()
                parts = name_str.split()
                if parts and parts[0].isdigit():
                    return parts[0]
                return None

            vendor_scores = []
            for vendor_name in vendor_names:
                price_idx = price_name_to_idx.get(vendor_name)
                timeliness_idx = timeliness_name_to_idx.get(vendor_name)

                if price_idx is None or timeliness_idx is None:
                    print(f"[COMPUTE_SCORES] Skipping {vendor_name}: not in model posterior", flush=True)
                    continue

                vendor_df = df_clean[df_clean["vendor_name"] == vendor_name]
                transaction_count = len(vendor_df)

                # Extract per-vendor posterior samples and flatten across chains
                price_samples = price_posterior_all[:, :, price_idx].flatten()
                timeliness_samples = timeliness_posterior_all[:, :, timeliness_idx].flatten()

                price_score = float(np.mean(price_samples))
                price_ci_lower = float(np.percentile(price_samples, 2.5))
                price_ci_upper = float(np.percentile(price_samples, 97.5))

                timeliness_score = -float(np.mean(timeliness_samples))
                timeliness_ci_lower = float(np.percentile(timeliness_samples, 2.5))
                timeliness_ci_upper = float(np.percentile(timeliness_samples, 97.5))

                combined_score = (-price_score + timeliness_score) / 2

                vendor_scores.append({
                    "vendor_name": str(vendor_name),
                    "vendor_id": extract_vendor_id(vendor_name),
                    "price_accuracy_score": price_score,
                    "price_accuracy_ci_lower": price_ci_lower,
                    "price_accuracy_ci_upper": price_ci_upper,
                    "timeliness_score": timeliness_score,
                    "timeliness_ci_lower": timeliness_ci_lower,
                    "timeliness_ci_upper": timeliness_ci_upper,
                    "combined_rank_score": combined_score,
                    "transaction_count": transaction_count,
                })

            print(f"[COMPUTE_SCORES] Created {len(vendor_scores)} vendor scores", flush=True)
            vendor_scores.sort(key=lambda x: x["combined_rank_score"], reverse=True)

            for idx, score in enumerate(vendor_scores):
                score["rank"] = idx + 1

            print(f"[COMPUTE_SCORES] Returning {len(vendor_scores)} scores", flush=True)
            return [VendorBHMScore(**score) for score in vendor_scores]

        except Exception as e:
            print(f"[COMPUTE_SCORES] ERROR: {e}", flush=True)
            traceback.print_exc()
            return []


    def fit_and_rank(
        self, 
        df: pd.DataFrame, 
        prior_checkpoint: Optional[Dict[str, Any]] = None
    ) -> BHMRankingsResponse:
        """Fit both models and compute vendor rankings."""
        try:
            price_fit_ok = self.fit_price_model(df, prior_checkpoint)
            if not price_fit_ok:
                raise ValueError("Failed to fit price accuracy model")
            
            timeliness_fit_ok = self.fit_timeliness_model(df, prior_checkpoint)
            if not timeliness_fit_ok:
                raise ValueError("Failed to fit timeliness model")

            convergence_status, convergence_warnings = self.check_convergence()
            vendor_rankings = self.compute_vendor_scores(df)

            return BHMRankingsResponse(
                session_id="",
                model_type="Bayesian Hierarchical Model",
                convergence_status=convergence_status,
                convergence_warnings=convergence_warnings,
                mcmc_iterations=self.mcmc_iterations,
                mcmc_chains=self.mcmc_chains,
                rankings=vendor_rankings,
                model_timestamp=datetime.utcnow(),
                posterior_version=None,
            )
        except Exception as e:
            raise ValueError(f"Failed to fit BHM models: {str(e)}")


    def save_posterior_checkpoint(self, model_year: str) -> Dict[str, Any]:
        """Save posteriors for use as priors in next year's model."""
        if self.price_idata is None or self.timeliness_idata is None:
            raise ValueError("Models must be fit before saving checkpoint")

        price_posteriors = self.price_idata.posterior["vendor_effects"].values
        timeliness_posteriors = self.timeliness_idata.posterior["vendor_effects"].values

        return {
            "model_year": model_year,
            "price_posteriors": price_posteriors.tolist(),
            "timeliness_posteriors": timeliness_posteriors.tolist(),
            "timestamp": datetime.utcnow().isoformat(),
            "prior_analysis_log": self.prior_analysis_log,
        }

    def get_mcmc_iteration_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed MCMC iteration counts and diagnostics."""
        info = {}
        
        if self.price_idata is not None:
            price_diag = MCMCDiagnostics(
                self.price_idata, 
                "price",
                self.mcmc_tuning,
                self.mcmc_iterations,
                self.mcmc_chains
            )
            info["price"] = {
                "iterations": price_diag.get_iteration_counts(),
                "diagnostics": price_diag.get_prior_likelihood_posterior_info(),
            }
        
        if self.timeliness_idata is not None:
            timeliness_diag = MCMCDiagnostics(
                self.timeliness_idata,
                "timeliness", 
                self.mcmc_tuning,
                self.mcmc_iterations,
                self.mcmc_chains
            )
            info["timeliness"] = {
                "iterations": timeliness_diag.get_iteration_counts(),
                "diagnostics": timeliness_diag.get_prior_likelihood_posterior_info(),
            }
        
        return info

    def generate_diagnostics_plots(self, output_dir: str = "bhm_diagnostics") -> bool:
        """Generate all MCMC diagnostic plots."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        print(f"[PLOTS] Generating plots in {output_dir}", flush=True)
        
        success = True
        
        if self.price_idata is not None:
            try:
                print(f"[PLOTS] Creating price model diagnostics plots...", flush=True)
                price_diag = MCMCDiagnostics(
                    self.price_idata,
                    "price",
                    self.mcmc_tuning,
                    self.mcmc_iterations,
                    self.mcmc_chains
                )
                success &= price_diag.create_trace_plot(f"{output_dir}/price_traces.png")
                success &= price_diag.create_iteration_summary_plot(f"{output_dir}/price_iterations_summary.png")
                success &= price_diag.create_burn_in_analysis_plot(f"{output_dir}/price_burnin_analysis.png")
                print(f"[PLOTS] Price plots created successfully", flush=True)
            except Exception as e:
                print(f"[PLOTS] Error creating price plots: {e}", flush=True)
                import traceback
                traceback.print_exc()
                success = False
        else:
            print(f"[PLOTS] price_idata is None, skipping price plots", flush=True)
        
        if self.timeliness_idata is not None:
            try:
                print(f"[PLOTS] Creating timeliness model diagnostics plots...", flush=True)
                timeliness_diag = MCMCDiagnostics(
                    self.timeliness_idata,
                    "timeliness",
                    self.mcmc_tuning,
                    self.mcmc_iterations,
                    self.mcmc_chains
                )
                success &= timeliness_diag.create_trace_plot(f"{output_dir}/timeliness_traces.png")
                success &= timeliness_diag.create_iteration_summary_plot(f"{output_dir}/timeliness_iterations_summary.png")
                success &= timeliness_diag.create_burn_in_analysis_plot(f"{output_dir}/timeliness_burnin_analysis.png")
                print(f"[PLOTS] Timeliness plots created successfully", flush=True)
            except Exception as e:
                print(f"[PLOTS] Error creating timeliness plots: {e}", flush=True)
                import traceback
                traceback.print_exc()
                success = False
        else:
            print(f"[PLOTS] timeliness_idata is None, skipping timeliness plots", flush=True)
        
        if success:
            print(f"[PLOTS] ✓ All MCMC diagnostics plots generated in {output_dir}/", flush=True)
        else:
            print(f"[PLOTS] ⚠ Some plots failed to generate", flush=True)
        
        return success

    def get_prior_audit_trail(self) -> Dict[str, Any]:
        """Return full prior analysis log for debugging/auditing."""
        return self.prior_analysis_log

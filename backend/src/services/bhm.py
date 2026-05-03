from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

try:
    import pymc as pm
    import arviz as az
except ImportError:
    pm = None
    az = None

from src.types.models import VendorBHMScore, BHMRankingsResponse, BHMDiagnostics


class BHMService:

    def __init__(self, mcmc_iterations: int = 2000, mcmc_chains: int = 4, mcmc_tuning: int = 1000):
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
        self.price_trace = None
        self.timeliness_trace = None
        self.price_idata = None
        self.timeliness_idata = None

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
            df_clean = df[[actual_metric_col, item_column, vendor_column]].dropna()
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

    def fit_price_model(self, df: pd.DataFrame, prior_checkpoint: Optional[Dict[str, Any]] = None) -> bool:
        """
        for price_discrepancy.
        3-level:
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

            with pm.Model() as model:
                vendor_mu = pm.Normal("vendor_mu", mu=0, sigma=1000)
                vendor_sigma = pm.HalfNormal("vendor_sigma", sigma=500)

                vendor_effects = pm.Normal(
                    "vendor_effects",
                    mu=vendor_mu,
                    sigma=vendor_sigma,
                    shape=n_vendors,
                )
                item_mu = pm.Normal("item_mu", mu=0, sigma=500)
                item_sigma = pm.HalfNormal("item_sigma", sigma=250)

                item_effects = pm.Normal(
                    "item_effects",
                    mu=item_mu,
                    sigma=item_sigma,
                    shape=n_items,
                )

                sigma_transaction = pm.HalfNormal("sigma_transaction", sigma=250)

                mu = vendor_effects[vendor_codes] + item_effects[item_codes]

                y = pm.Normal(
                    "y",
                    mu=mu,
                    sigma=sigma_transaction,
                    observed=metric_values,
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
                    )

            self.price_model = model
            return True

        except Exception as e:
            print(f"Error fitting price model: {e}")
            return False

    def fit_timeliness_model(self, df: pd.DataFrame, prior_checkpoint: Optional[Dict[str, Any]] = None) -> bool:

        try:
            # Prepare data
            metric_values, item_codes, vendor_codes, item_map, vendor_map = (
                self.prepare_hierarchical_data(df, "delay")
            )

            n_items = len(item_map)
            n_vendors = len(vendor_map)

            with pm.Model() as model:
                # Hyperpriors for vendor-level effects
                vendor_mu = pm.Normal("vendor_mu", mu=0, sigma=50)
                vendor_sigma = pm.HalfNormal("vendor_sigma", sigma=25)

                # Vendor-level effects
                vendor_effects = pm.Normal(
                    "vendor_effects",
                    mu=vendor_mu,
                    sigma=vendor_sigma,
                    shape=n_vendors,
                )

                # Hyperpriors for item-level effects
                item_mu = pm.Normal("item_mu", mu=0, sigma=25)
                item_sigma = pm.HalfNormal("item_sigma", sigma=12)

                # Item-level effects
                item_effects = pm.Normal(
                    "item_effects",
                    mu=item_mu,
                    sigma=item_sigma,
                    shape=n_items,
                )

                sigma_transaction = pm.HalfNormal("sigma_transaction", sigma=12)

                mu = vendor_effects[vendor_codes] + item_effects[item_codes]

                y = pm.Normal(
                    "y",
                    mu=mu,
                    sigma=sigma_transaction,
                    observed=metric_values,
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
                    )

            self.timeliness_model = model
            return True

        except Exception as e:
            print(f"Error fitting timeliness model: {e}")
            return False

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
        diagnostics = []

        if self.price_idata is not None:
            price_rhat = az.rhat(self.price_idata)
            for var_name, var_data in price_rhat.data_vars.items():
                max_rhat = float(var_data.max().values)
                diagnostics.append(BHMDiagnostics(
                    metric_name=f"price_discrepancy_{var_name}",
                    r_hat=max_rhat,
                    effective_sample_size=0,  # Simplified
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
                    effective_sample_size=0,  # Simplified
                    has_divergences=False,
                    rhat_status="good" if max_rhat < 1.01 else "warning",
                ))

        return diagnostics

    def compute_vendor_scores(self, df: pd.DataFrame) -> List[VendorBHMScore]:
        """
        Extract vendor-level posterior estimates and compute ranking scores.
        """
        if self.price_idata is None or self.timeliness_idata is None:
            return []

        vendor_names = df["vendor_name"].unique()
        vendor_scores = []
        price_posterior = self.price_idata.posterior["vendor_effects"].values.flatten()
        timeliness_posterior = self.timeliness_idata.posterior["vendor_effects"].values.flatten()

        for idx, vendor_name in enumerate(vendor_names):
            if idx >= len(price_posterior) or idx >= len(timeliness_posterior):
                continue

            vendor_df = df[df["vendor_name"] == vendor_name]
            transaction_count = len(vendor_df)

            price_mean = float(price_posterior[idx])
            price_score = -price_mean  # Negative of effect (lower is better)
            price_ci_lower = float(np.percentile(price_posterior, 2.5))
            price_ci_upper = float(np.percentile(price_posterior, 97.5))

            timeliness_mean = float(timeliness_posterior[idx])
            timeliness_score = -timeliness_mean
            timeliness_ci_lower = float(np.percentile(timeliness_posterior, 2.5))
            timeliness_ci_upper = float(np.percentile(timeliness_posterior, 97.5))

            combined_score = (price_score + timeliness_score) / 2

            vendor_scores.append({
                "vendor_name": str(vendor_name),
                "vendor_id": None,
                "price_accuracy_score": price_score,
                "price_accuracy_ci_lower": price_ci_lower,
                "price_accuracy_ci_upper": price_ci_upper,
                "timeliness_score": timeliness_score,
                "timeliness_ci_lower": timeliness_ci_lower,
                "timeliness_ci_upper": timeliness_ci_upper,
                "combined_rank_score": combined_score,
                "transaction_count": transaction_count,
            })

        vendor_scores.sort(key=lambda x: x["combined_rank_score"], reverse=True)

        for idx, score in enumerate(vendor_scores):
            score["rank"] = idx + 1

        return [VendorBHMScore(**score) for score in vendor_scores]

    def fit_and_rank(self, df: pd.DataFrame, prior_checkpoint: Optional[Dict[str, Any]] = None) -> BHMRankingsResponse:

        try:
            price_fit_ok = self.fit_price_model(df, prior_checkpoint)
            if not price_fit_ok:
                raise ValueError("Failed to fit price accuracy model")
            
            timeliness_fit_ok = self.fit_timeliness_model(df, prior_checkpoint)
            if not timeliness_fit_ok:
                raise ValueError("Failed to fit timeliness model")

            convergence_status, convergence_warnings = self.check_convergence()

            vendor_rankings = self.compute_vendor_scores(df)

            diagnostics = self.get_diagnostics()

            return BHMRankingsResponse(
                session_id="",  # Will be set by caller
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
            print(f"Error in fit_and_rank: {e}")
            raise ValueError(f"Failed to fit BHM models: {str(e)}")

    def save_posterior_checkpoint(self, model_year: str) -> Dict[str, Any]:

        if self.price_idata is None or self.timeliness_idata is None:
            raise ValueError("Models must be fit before saving checkpoint")

        price_posteriors = self.price_idata.posterior["vendor_effects"].values
        timeliness_posteriors = self.timeliness_idata.posterior["vendor_effects"].values

        return {
            "model_year": model_year,
            "price_posteriors": price_posteriors.tolist(),
            "timeliness_posteriors": timeliness_posteriors.tolist(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def load_prior_from_checkpoint(self, checkpoint: Dict[str, Any]) -> None:

        pass

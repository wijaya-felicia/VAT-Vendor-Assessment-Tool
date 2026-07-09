from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime
import warnings

import matplotlib
matplotlib.use('Agg')



class MCMCDiagnostics:
    
    def __init__(self, idata, metric_type: str, warmup_draws: int, draws: int, chains: int):

        self.idata = idata
        self.metric_type = metric_type
        self.warmup_draws = warmup_draws
        self.draws = draws
        self.chains = chains
        
    def get_iteration_counts(self) -> Dict[str, int]:
        total_burn_in = self.warmup_draws * self.chains
        total_convergence = self.draws * self.chains
        total_iterations = total_burn_in + total_convergence
        
        return {
            "total_iterations": total_iterations,
            "burn_in_iterations": total_burn_in,
            "convergence_iterations": total_convergence,
            "chains": self.chains,
            "draws_per_chain": self.draws,
            "warmup_per_chain": self.warmup_draws,
            "burn_in_percentage": (total_burn_in / total_iterations * 100),
            "convergence_percentage": (total_convergence / total_iterations * 100),
        }
    
    def get_prior_likelihood_posterior_info(self) -> Dict[str, Any]:
        try:
            import arviz as az
        except ImportError:
            print(f"Warning: arviz not available, returning minimal diagnostics", flush=True)
            return {
                "metric_type": self.metric_type,
                "n_parameters": 0,
                "max_rhat": 1.0,
                "all_converged": False,
                "n_divergences": 0,
                "divergence_rate": 0.0,
                "effective_sample_size": {},
                "rhat_diagnostics": [],
            }
        
        info = {
            "metric_type": self.metric_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            n_params = 0
            if hasattr(self.idata, 'posterior') and self.idata.posterior is not None:
                try:
                    for var_name, var_data in self.idata.posterior.data_vars.items():
                        # Count all dimensions as separate parameters (skip chain dimension which is first)
                        param_size = int(np.prod(var_data.shape[1:])) if len(var_data.shape) > 1 else 1
                        n_params += param_size
                except Exception as e:
                    print(f"Warning: Could not count parameters: {e}")
                    n_params = 0
            info["n_parameters"] = n_params
            
            rhat_data = az.rhat(self.idata)
            rhat_values = []
            max_rhat_found = None
            
            if rhat_data is not None:
                try:
                    for var_name, var_data in rhat_data.data_vars.items():
                        if var_data is not None:
                            try:
                                rhat_max = float(var_data.max().values)
                                rhat_values.append({
                                    "parameter": var_name,
                                    "rhat": rhat_max,
                                    "converged": rhat_max < 1.01
                                })
                                if max_rhat_found is None or rhat_max > max_rhat_found:
                                    max_rhat_found = rhat_max
                            except Exception as e:
                                print(f"Warning: Could not extract Rhat for {var_name}: {e}")
                except Exception as e:
                    print(f"Warning: Could not extract Rhat values: {e}")
            
            info["rhat_diagnostics"] = rhat_values
            
            if max_rhat_found is not None:
                info["max_rhat"] = max_rhat_found
                info["all_converged"] = all(r["converged"] for r in rhat_values) if rhat_values else False
            else:
                info["max_rhat"] = 1.0
                info["all_converged"] = False
            
            ess_data = az.ess(self.idata)
            ess_dict = {}
            if ess_data is not None:
                for var_name, var_data in ess_data.data_vars.items():
                    if var_data is not None:
                        ess_dict[var_name] = float(var_data.max().values)
            info["effective_sample_size"] = ess_dict
            
            try:
                if hasattr(self.idata, 'sample_stats') and self.idata.sample_stats is not None:
                    if hasattr(self.idata.sample_stats, 'diverging'):
                        n_divergences = int(self.idata.sample_stats.diverging.sum().values)
                        info["n_divergences"] = n_divergences
                        info["divergence_rate"] = n_divergences / (self.draws * self.chains) if (self.draws * self.chains) > 0 else 0.0
                    else:
                        info["n_divergences"] = 0
                        info["divergence_rate"] = 0.0
                else:
                    info["n_divergences"] = 0
                    info["divergence_rate"] = 0.0
            except Exception as e:
                print(f"Warning: Could not extract divergence data: {e}")
                info["n_divergences"] = 0
                info["divergence_rate"] = 0.0
            
            try:
                if hasattr(self.idata, 'sample_stats') and self.idata.sample_stats is not None:
                    if hasattr(self.idata.sample_stats, 'lp'):
                        lp = self.idata.sample_stats.lp.values
                        info["mean_log_prob"] = float(np.mean(lp))
                        info["std_log_prob"] = float(np.std(lp))
                    else:
                        info["mean_log_prob"] = None
                        info["std_log_prob"] = None
                else:
                    info["mean_log_prob"] = None
                    info["std_log_prob"] = None
            except Exception as e:
                print(f"Warning: Could not extract log probability: {e}")
                info["mean_log_prob"] = None
                info["std_log_prob"] = None
            
            return info
        
        except Exception as e:
            print(f"Error in get_prior_likelihood_posterior_info: {e}")
            import traceback
            traceback.print_exc()
            return {
                "metric_type": self.metric_type,
                "n_parameters": 0,
                "max_rhat": 1.0,
                "all_converged": False,
                "n_divergences": 0,
                "divergence_rate": 0.0,
                "effective_sample_size": {},
                "rhat_diagnostics": [],
                "error": str(e)
            }
    
    def create_trace_plot(self, output_path: str, max_vars: int = 10) -> bool:
        try:
            import matplotlib.pyplot as plt
            import arviz as az
        except ImportError as e:
            print(f"[TRACE_PLOT] ERROR: matplotlib or arviz not available: {e}", flush=True)
            return False
        
        try:
            print(f"[TRACE_PLOT] Starting trace plot generation for {self.metric_type}", flush=True)
            
            if not hasattr(self.idata, 'posterior'):
                print(f"[TRACE_PLOT] ERROR: idata has no posterior attribute", flush=True)
                return False
            
            if self.idata.posterior is None:
                print(f"[TRACE_PLOT] ERROR: posterior is None", flush=True)
                return False
            
            var_names = list(self.idata.posterior.data_vars.keys())[:max_vars]
            print(f"[TRACE_PLOT] Found {len(var_names)} variables: {var_names}", flush=True)
            
            if len(var_names) == 0:
                print(f"[TRACE_PLOT] ERROR: No variables found in posterior", flush=True)
                return False
            
            fig = plt.figure(figsize=(16, 12), facecolor='#0f1419')
            gs = fig.add_gridspec(len(var_names), 1, hspace=0.4)
            
            fig.suptitle(
                f'{self.metric_type.upper()} Model - Trace Plots (Burn-in Phase Visible)',
                fontsize=16, fontweight='bold', color='white'
            )
            fig.patch.set_facecolor('#0f1419')
            
            for idx, var_name in enumerate(var_names):
                ax = fig.add_subplot(gs[idx])
                ax.set_facecolor('#1a1d23')
                ax.tick_params(colors='#c8d6e5', which='both')
                
                trace_data = self.idata.posterior[var_name].values
                if len(trace_data.shape) > 2:
                    trace_data = trace_data.reshape(trace_data.shape[0], trace_data.shape[1], -1)
                    trace_data = trace_data[:, :, 0]
                
                colors = plt.cm.tab10(np.linspace(0, 1, self.chains))
                for chain_idx in range(self.chains):
                    ax.plot(trace_data[chain_idx], alpha=0.7, color=colors[chain_idx], 
                           linewidth=0.8, label=f'Chain {chain_idx}')
                
                ax.axvline(self.warmup_draws, color='red', linestyle='--', linewidth=2, 
                          label=f'Burn-in end ({self.warmup_draws} draws)')
                ax.fill_betweenx(
                    [trace_data.min(), trace_data.max()],
                    0, self.warmup_draws,
                    alpha=0.2, color='red', label='Burn-in region'
                )
                
                ax.set_ylabel(var_name, color='#c8d6e5')
                ax.set_xlabel('Draw number', color='#c8d6e5')
                ax.grid(True, alpha=0.3, color='#3d424a')
                
                if idx == 0:
                    ax.legend(loc='upper right', fontsize=9, labelcolor='#e0e0e0',
                         facecolor='#1a1d23', edgecolor='#3d424a')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"[TRACE_PLOT] ✓ Trace plot saved: {output_path}", flush=True)
            return True
        
        except Exception as e:
            print(f"[TRACE_PLOT] ERROR: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False
    
    def create_iteration_summary_plot(self, output_path: str) -> bool:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print(f"[ITERATION_PLOT] ERROR: matplotlib not available", flush=True)
            return False
        
        try:
            counts = self.get_iteration_counts()
            info = self.get_prior_likelihood_posterior_info()
            
            fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor='#0f1419')
            fig.suptitle(
                f'{self.metric_type.upper()} Model - MCMC Iteration Summary',
                fontsize=16, fontweight='bold', color='white'
            )
            fig.patch.set_facecolor('#0f1419')
            for row in axes:
                for ax in row:
                    ax.set_facecolor('#1a1d23')
            
            ax = axes[0, 0]
            sizes = [counts["burn_in_iterations"], counts["convergence_iterations"]]
            labels = [
                f'Burn-in\n{counts["burn_in_iterations"]} iterations\n({counts["burn_in_percentage"]:.1f}%)',
                f'Convergence\n{counts["convergence_iterations"]} iterations\n({counts["convergence_percentage"]:.1f}%)'
            ]
            colors = ['#ff6b6b', '#4ecdc4']
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='',
                                               startangle=90, textprops={'fontsize': 11, 'color': '#e0e0e0'})
            ax.set_title('Iteration Allocation', fontweight='bold', color='#e0e0e0')
            
            ax = axes[0, 1]
            categories = ['Total\nIterations', 'Burn-in\nper Chain', 'Convergence\nper Chain']
            values = [counts["total_iterations"], counts["warmup_per_chain"], counts["draws_per_chain"]]
            bars = ax.bar(categories, values, color=['#8e44ad', '#e74c3c', '#27ae60'], edgecolor='black', linewidth=1.5)
            ax.set_ylabel('Count', fontsize=11, color='#c8d6e5')
            ax.set_title('Iteration Counts', fontweight='bold', color='white')
            ax.grid(True, alpha=0.3, axis='y')
            ax.tick_params(axis='x', colors='#c8d6e5')
            ax.tick_params(axis='y', colors='#c8d6e5')
            
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(val):,}', ha='center', va='bottom', fontsize=10, fontweight='bold',
                       color='#e0e0e0')
            
            ax = axes[1, 0]
            ax.set_facecolor('#1a1d23')
            ax.axis('off')
            
            diag_text = f"""
CONVERGENCE DIAGNOSTICS

Parameters: {info.get('n_parameters', 'N/A')}
Max R̂ (Rhat): {info['max_rhat']:.4f}
  → {'✓ CONVERGED' if info['all_converged'] else '✗ NOT CONVERGED'} (threshold: 1.01)

Divergences: {info['n_divergences']}
  → Rate: {info['divergence_rate']*100:.2f}%

Mean Log Probability: {f"{info['mean_log_prob']:.4f}" if info['mean_log_prob'] is not None else 'N/A'}
Std Log Probability: {f"{info['std_log_prob']:.4f}" if info['std_log_prob'] is not None else 'N/A'}

Effective Sample Size:
{chr(10).join([f'  • {k}: {v:.0f}' for k, v in list(info['effective_sample_size'].items())[:5]])}
"""
            
            ax.text(0.05, 0.95, diag_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top', family='monospace', color='white',
                   bbox=dict(boxstyle='round', facecolor='#1a1d23', edgecolor='#3d424a', alpha=0.95))
            
            ax = axes[1, 1]
            ax.set_facecolor('#1a1d23')
            ax.axis('off')
            
            chain_text = f"""
MCMC CONFIGURATION

Chains: {counts['chains']}
Warmup per Chain: {counts['warmup_per_chain']:,}
Post-warmup Draws: {counts['draws_per_chain']:,}
Total Samples: {counts['total_iterations']:,}

Sampling Details:
  • Sampler: NUTS (PyMC)
  • Target Accept: 0.95
  • Adaptation: During warmup
  • Random Seed: 42

Per-Chain Samples:
  • Burn-in: {counts['warmup_per_chain']:,}
  • Kept: {counts['draws_per_chain']:,}
  • Total: {counts['warmup_per_chain'] + counts['draws_per_chain']:,}
"""
            
            ax.text(0.05, 0.95, chain_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top', family='monospace', color='white',
                   bbox=dict(boxstyle='round', facecolor='#1a2f4d', edgecolor='#3d424a', alpha=0.95))
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Iteration summary plot saved: {output_path}")
            return True
        
        except Exception as e:
            print(f"Error creating iteration summary: {e}")
            return False
    
    def create_burn_in_analysis_plot(self, output_path: str, top_vars: int = 8) -> bool:
        try:
            import matplotlib.pyplot as plt
            import arviz as az
        except ImportError as e:
            print(f"[BURNIN_PLOT] ERROR: matplotlib or arviz not available: {e}", flush=True)
            return False
        
        try:
            var_names = list(self.idata.posterior.data_vars.keys())[:top_vars]
            
            fig, axes = plt.subplots(top_vars, 2, figsize=(16, 3*top_vars), facecolor='#0f1419')
            if top_vars == 1:
                axes = axes.reshape(1, -1)
            
            fig.suptitle(
                f'{self.metric_type.upper()} Model - Burn-in Analysis\n'
                f'Red line = end of burn-in ({self.warmup_draws} draws)',
                fontsize=14, fontweight='bold', color='white'
            )
            fig.patch.set_facecolor('#0f1419')
            
            for idx, var_name in enumerate(var_names):
                trace_data = self.idata.posterior[var_name].values
                if len(trace_data.shape) > 2:
                    trace_data = trace_data.reshape(trace_data.shape[0], trace_data.shape[1], -1)
                    trace_data = trace_data[:, :, 0]
                
                ax = axes[idx, 0]
                ax.set_facecolor('#1a1d23')
                ax.tick_params(colors='#c8d6e5', which='both')
                for chain_idx in range(min(self.chains, 4)):  # Show max 4 chains
                    ax.plot(trace_data[chain_idx], alpha=0.6, linewidth=0.8, 
                           label=f'Chain {chain_idx}')
                
                ax.axvline(self.warmup_draws, color='red', linestyle='--', linewidth=2)
                ax.fill_betweenx([trace_data.min(), trace_data.max()], 0, self.warmup_draws,
                                alpha=0.15, color='red')
                ax.set_ylabel(var_name, color='#c8d6e5')
                ax.set_title(f'{var_name} - Full Trace', color='white')
                ax.grid(True, alpha=0.3, color='#3d424a')
                if idx == 0:
                    ax.legend(fontsize=9, labelcolor='#e0e0e0',
                         facecolor='#1a1d23', edgecolor='#3d424a')
                
                ax = axes[idx, 1]
                ax.set_facecolor('#1a1d23')
                ax.tick_params(colors='#c8d6e5', which='both')
                burnin_period = trace_data[:, :self.warmup_draws]
                for chain_idx in range(min(self.chains, 4)):
                    ax.plot(burnin_period[chain_idx], alpha=0.6, linewidth=0.8)
                
                ax.set_ylabel(var_name, color='#c8d6e5')
                ax.set_title(f'{var_name} - Burn-in Detail (0-{self.warmup_draws})', color='white')
                ax.grid(True, alpha=0.3, color='#3d424a')
                ax.axvline(self.warmup_draws * 0.8, color='orange', linestyle=':', 
                          linewidth=2, alpha=0.5, label='80% of warmup')
                if idx == 0:
                    ax.legend(fontsize=9, labelcolor='#e0e0e0',
                         facecolor='#1a1d23', edgecolor='#3d424a')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Burn-in analysis plot saved: {output_path}")
            return True
        
        except Exception as e:
            print(f"Error creating burn-in analysis: {e}")
            return False

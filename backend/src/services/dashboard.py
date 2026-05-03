from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from src.types.models import DashboardMetrics, VendorStats


class DashboardService:

    def __init__(self):
        pass

    def compute_total_spending(self, df: pd.DataFrame) -> float:

        if "total_price_po" in df.columns:
            return float(df["total_price_po"].sum())
        elif "total_price" in df.columns:
            return float(df["total_price"].sum())
        elif "po_total_price" in df.columns:
            return float(df["po_total_price"].sum())
        return 0.0

    def compute_average_transaction_value(self, df: pd.DataFrame) -> float:

        total_spending = self.compute_total_spending(df)
        transaction_count = len(df)
        return total_spending / transaction_count if transaction_count > 0 else 0.0

    def compute_price_accuracy_stats(self, df: pd.DataFrame) -> Dict[str, float]:

        if "price_discrepancy" not in df.columns:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        discrepancies = df["price_discrepancy"].dropna()

        return {
            "mean": float(discrepancies.mean()),
            "std": float(discrepancies.std()),
            "min": float(discrepancies.min()),
            "max": float(discrepancies.max()),
        }

    def compute_timeliness_stats(self, df: pd.DataFrame) -> Dict[str, float]:

        delay_col = None
        if "delay_days" in df.columns:
            delay_col = "delay_days"
        elif "delay" in df.columns:
            delay_col = "delay"
        
        if delay_col is None:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        delays = df[delay_col].dropna()

        return {
            "mean": float(delays.mean()),
            "std": float(delays.std()),
            "min": float(delays.min()),
            "max": float(delays.max()),
        }

    def compute_per_vendor_stats(self, df: pd.DataFrame) -> List[Dict[str, Any]]:

        vendor_stats = []

        if "vendor_name" not in df.columns:
            return vendor_stats

        for vendor_name, vendor_df in df.groupby("vendor_name"):

            transaction_count = len(vendor_df)

            total_spending = self.compute_total_spending(vendor_df)
            average_spending = total_spending / transaction_count if transaction_count > 0 else 0.0

            if "price_discrepancy" in vendor_df.columns:
                discrepancies = vendor_df["price_discrepancy"].dropna()
                price_discrepancy_mean = float(discrepancies.mean()) if len(discrepancies) > 0 else 0.0
                price_discrepancy_std = float(discrepancies.std()) if len(discrepancies) > 0 else 0.0
            else:
                price_discrepancy_mean = 0.0
                price_discrepancy_std = 0.0

            delay_col = None
            if "delay_days" in vendor_df.columns:
                delay_col = "delay_days"
            elif "delay" in vendor_df.columns:
                delay_col = "delay"
            
            if delay_col is not None:
                delays = vendor_df[delay_col].dropna()
                delay_mean = float(delays.mean()) if len(delays) > 0 else 0.0
                delay_std = float(delays.std()) if len(delays) > 0 else 0.0
            else:
                delay_mean = 0.0
                delay_std = 0.0

            vendor_stats.append({
                "vendor_name": str(vendor_name),
                "transaction_count": transaction_count,
                "total_spending": total_spending,
                "average_spending": average_spending,
                "price_discrepancy_mean": price_discrepancy_mean,
                "price_discrepancy_std": price_discrepancy_std,
                "delay_mean": delay_mean,
                "delay_std": delay_std,
            })

        return vendor_stats

    def get_aggregated_metrics(self, df: pd.DataFrame, session_id: str) -> DashboardMetrics:

        total_spending = self.compute_total_spending(df)
        transaction_count = len(df)
        average_transaction_value = self.compute_average_transaction_value(df)
        vendor_count = df["vendor_name"].nunique() if "vendor_name" in df.columns else 0

        price_acc_stats = self.compute_price_accuracy_stats(df)

        delay_stats = self.compute_timeliness_stats(df)

        per_vendor = self.compute_per_vendor_stats(df)

        vendor_stats_list = [
            VendorStats(**stats)
            for stats in per_vendor
        ]

        return DashboardMetrics(
            session_id=session_id,
            total_transactions=transaction_count,
            total_spending=total_spending,
            average_transaction_value=average_transaction_value,
            vendor_count=vendor_count,
            price_discrepancy_mean=price_acc_stats["mean"],
            price_discrepancy_std=price_acc_stats["std"],
            delay_mean=delay_stats["mean"],
            delay_std=delay_stats["std"],
            vendors=vendor_stats_list,
        )

    def get_vendor_comparison_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:

        per_vendor = self.compute_per_vendor_stats(df)

        return [
            {
                "vendor_name": stats["vendor_name"],
                "total_spending": stats["total_spending"],
                "transaction_count": stats["transaction_count"],
                "avg_spending": stats["average_spending"],
            }
            for stats in per_vendor
        ]

    def get_price_trend_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:

        if "price_discrepancy" not in df.columns or "vendor_name" not in df.columns:
            return []

        trend_data = []

        for vendor_name, vendor_df in df.groupby("vendor_name"):
            discrepancies = vendor_df["price_discrepancy"].dropna()

            if len(discrepancies) > 0:
                trend_data.append({
                    "vendor_name": str(vendor_name),
                    "mean_price_discrepancy": float(discrepancies.mean()),
                    "min_price_discrepancy": float(discrepancies.min()),
                    "max_price_discrepancy": float(discrepancies.max()),
                    "count": len(discrepancies),
                })

        return trend_data

    def get_delay_distribution(self, df: pd.DataFrame) -> List[Dict[str, Any]]:

        delay_col = None
        if "delay_days" in df.columns:
            delay_col = "delay_days"
        elif "delay" in df.columns:
            delay_col = "delay"
        
        if delay_col is None or "vendor_name" not in df.columns:
            return []

        bins = [-float('inf'), 0, 5, 10, 15, 20, 30, float('inf')]
        labels = ["Early", "0-5 days", "5-10 days", "10-15 days", "15-20 days", "20-30 days", "30+ days"]

        distribution = []

        for vendor_name, vendor_df in df.groupby("vendor_name"):
            delays = vendor_df[delay_col].dropna()

            if len(delays) > 0:
                # Bin the delays
                binned = pd.cut(delays, bins=bins, labels=labels, right=False)
                counts = binned.value_counts().sort_index()

                for label, count in counts.items():
                    distribution.append({
                        "vendor_name": str(vendor_name),
                        "delay_range": str(label),
                        "count": int(count),
                    })

        return distribution

    def get_vendor_performance_matrix(self, df: pd.DataFrame) -> List[Dict[str, Any]]:

        per_vendor = self.compute_per_vendor_stats(df)
        price_acc_stats = self.compute_price_accuracy_stats(df)
        delay_stats = self.compute_timeliness_stats(df)

        matrix = []

        for vendor_stats in per_vendor:
            price_score = 100 - min(
                100,
                (abs(vendor_stats["price_discrepancy_mean"]) / max(1, abs(price_acc_stats["max"]))) * 100
            )

            timeliness_score = 100 - min(
                100,
                (vendor_stats["delay_mean"] / max(1, delay_stats["max"])) * 100
            )

            combined_score = (price_score + timeliness_score) / 2

            matrix.append({
                "vendor_name": vendor_stats["vendor_name"],
                "price_accuracy_score": round(price_score, 2),
                "timeliness_score": round(timeliness_score, 2),
                "combined_score": round(combined_score, 2),
                "transaction_count": vendor_stats["transaction_count"],
            })

        matrix.sort(key=lambda x: x["combined_score"], reverse=True)

        return matrix

import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from src.database import (
    SessionLocal,
    UploadRecord,
    ProcessedData,
    VendorMetric,
    SessionData,
)


class StorageManager(ABC):

    @abstractmethod
    def save_session_data(
        self,
        session_id: str,
        merged_df: pd.DataFrame,
        po_row_count: int,
        oc_row_count: int,
        ship_row_count: int,
        metrics: Dict[str, float],
    ) -> bool:
        pass

    @abstractmethod
    def save_persistent_data(
        self,
        session_id: str,
        user_id: str,
        merged_df: pd.DataFrame,
        po_row_count: int,
        oc_row_count: int,
        ship_row_count: int,
        metrics: Dict[str, float],
        vendor_metrics: List[Dict[str, Any]],
    ) -> bool:
        pass

    @abstractmethod
    def retrieve_data(self, session_id: str) -> Optional[pd.DataFrame]:
        pass

    @abstractmethod
    def retrieve_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass


class SessionBasedStorage(StorageManager):

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_expiry: Dict[str, datetime] = {}

    def save_session_data(
        self,
        session_id: str,
        merged_df: pd.DataFrame,
        po_row_count: int,
        oc_row_count: int,
        ship_row_count: int,
        metrics: Dict[str, float],
    ) -> bool:
        try:
            self.sessions[session_id] = {
                "merged_df": merged_df,
                "po_row_count": po_row_count,
                "oc_row_count": oc_row_count,
                "ship_row_count": ship_row_count,
                "metrics": metrics,
                "created_at": datetime.utcnow(),
            }
            self.session_expiry[session_id] = datetime.utcnow() + timedelta(hours=24)
            return True
        except Exception as e:
            print(f"Error saving session data: {e}")
            return False

    def save_persistent_data(
        self,
        session_id: str,
        user_id: str,
        merged_df: pd.DataFrame,
        po_row_count: int,
        oc_row_count: int,
        ship_row_count: int,
        metrics: Dict[str, float],
        vendor_metrics: List[Dict[str, Any]],
    ) -> bool:
        return False

    def retrieve_data(self, session_id: str) -> Optional[pd.DataFrame]:
        if session_id not in self.sessions:
            return None

        if datetime.utcnow() > self.session_expiry[session_id]:
            del self.sessions[session_id]
            del self.session_expiry[session_id]
            return None

        return self.sessions[session_id]["merged_df"]

    def retrieve_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id not in self.sessions:
            return None

        if datetime.utcnow() > self.session_expiry[session_id]:
            del self.sessions[session_id]
            del self.session_expiry[session_id]
            return None

        return self.sessions[session_id].get("metrics", {})

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        active_sessions = []
        expired_sessions = []

        for session_id, data in self.sessions.items():
            if datetime.utcnow() > self.session_expiry[session_id]:
                expired_sessions.append(session_id)
            else:
                active_sessions.append({
                    "session_id": session_id,
                    "created_at": data["created_at"],
                    "row_count": len(data["merged_df"]),
                })

        for session_id in expired_sessions:
            del self.sessions[session_id]
            del self.session_expiry[session_id]

        return active_sessions

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            del self.session_expiry[session_id]
            return True
        return False


class PersistentStorage(StorageManager):

    def __init__(self):
        self.db = SessionLocal()

    def save_session_data(
        self,
        session_id: str,
        merged_df: pd.DataFrame,
        po_row_count: int,
        oc_row_count: int,
        ship_row_count: int,
        metrics: Dict[str, float],
    ) -> bool:
        try:
            # Create upload record
            upload_record = UploadRecord(
                session_id=session_id,
                po_row_count=po_row_count,
                oc_row_count=oc_row_count,
                ship_row_count=ship_row_count,
                merged_row_count=len(merged_df),
                status="completed",
            )
            self.db.add(upload_record)
            self.db.commit()

            processed_data = ProcessedData(
                upload_id=upload_record.id,
                total_spending=metrics.get("total_spending", 0.0),
                average_transaction_value=metrics.get("average_transaction_value", 0.0),
                vendor_count=metrics.get("vendor_count", 0),
                transaction_count=len(merged_df),
                price_discrepancy_mean=metrics.get("price_discrepancy_mean", 0.0),
                price_discrepancy_std=metrics.get("price_discrepancy_std", 0.0),
                price_discrepancy_min=metrics.get("price_discrepancy_min", 0.0),
                price_discrepancy_max=metrics.get("price_discrepancy_max", 0.0),
                delay_mean=metrics.get("delay_mean", 0.0),
                delay_std=metrics.get("delay_std", 0.0),
                delay_min=metrics.get("delay_min", 0.0),
                delay_max=metrics.get("delay_max", 0.0),
            )
            self.db.add(processed_data)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            print(f"Error saving persistent data: {e}")
            return False

    def save_persistent_data(
        self,
        session_id: str,
        user_id: str,
        merged_df: pd.DataFrame,
        po_row_count: int,
        oc_row_count: int,
        ship_row_count: int,
        metrics: Dict[str, float],
        vendor_metrics: List[Dict[str, Any]],
    ) -> bool:
        try:
            upload_record = UploadRecord(
                session_id=session_id,
                user_id=user_id,
                po_row_count=po_row_count,
                oc_row_count=oc_row_count,
                ship_row_count=ship_row_count,
                merged_row_count=len(merged_df),
                status="completed",
            )
            self.db.add(upload_record)
            self.db.commit()

            processed_data = ProcessedData(
                upload_id=upload_record.id,
                total_spending=metrics.get("total_spending", 0.0),
                average_transaction_value=metrics.get("average_transaction_value", 0.0),
                vendor_count=metrics.get("vendor_count", 0),
                transaction_count=len(merged_df),
                price_discrepancy_mean=metrics.get("price_discrepancy_mean", 0.0),
                price_discrepancy_std=metrics.get("price_discrepancy_std", 0.0),
                price_discrepancy_min=metrics.get("price_discrepancy_min", 0.0),
                price_discrepancy_max=metrics.get("price_discrepancy_max", 0.0),
                delay_mean=metrics.get("delay_mean", 0.0),
                delay_std=metrics.get("delay_std", 0.0),
                delay_min=metrics.get("delay_min", 0.0),
                delay_max=metrics.get("delay_max", 0.0),
            )
            self.db.add(processed_data)

            for vendor_metric in vendor_metrics:
                metric = VendorMetric(
                    processed_data=processed_data,
                    vendor_name=vendor_metric.get("vendor_name"),
                    vendor_id=vendor_metric.get("vendor_id"),
                    transaction_count=vendor_metric.get("transaction_count", 0),
                    total_spending=vendor_metric.get("total_spending", 0.0),
                    average_spending=vendor_metric.get("average_spending", 0.0),
                    price_discrepancy_mean=vendor_metric.get("price_discrepancy_mean", 0.0),
                    price_discrepancy_std=vendor_metric.get("price_discrepancy_std", 0.0),
                    delay_mean=vendor_metric.get("delay_mean", 0.0),
                    delay_std=vendor_metric.get("delay_std", 0.0),
                )
                self.db.add(metric)

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            print(f"Error saving persistent data: {e}")
            return False

    def retrieve_data(self, session_id: str) -> Optional[pd.DataFrame]:
        try:
            upload_record = self.db.query(UploadRecord).filter(
                UploadRecord.session_id == session_id
            ).first()

            if not upload_record:
                return None

            processed_data = self.db.query(ProcessedData).filter(
                ProcessedData.upload_id == upload_record.id
            ).first()

            if processed_data and processed_data.merged_data_json:
                return pd.DataFrame(processed_data.merged_data_json)

            return None

        except Exception as e:
            print(f"Error retrieving data: {e}")
            return None

    def retrieve_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            upload_record = self.db.query(UploadRecord).filter(
                UploadRecord.session_id == session_id
            ).first()

            if not upload_record:
                return None

            processed_data = self.db.query(ProcessedData).filter(
                ProcessedData.upload_id == upload_record.id
            ).first()

            if not processed_data:
                return None

            return {
                "total_spending": processed_data.total_spending,
                "average_transaction_value": processed_data.average_transaction_value,
                "vendor_count": processed_data.vendor_count,
                "transaction_count": processed_data.transaction_count,
                "price_discrepancy_mean": processed_data.price_discrepancy_mean,
                "price_discrepancy_std": processed_data.price_discrepancy_std,
                "delay_mean": processed_data.delay_mean,
                "delay_std": processed_data.delay_std,
            }

        except Exception as e:
            print(f"Error retrieving metrics: {e}")
            return None

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            query = self.db.query(UploadRecord)

            if user_id:
                query = query.filter(UploadRecord.user_id == user_id)

            records = query.order_by(UploadRecord.created_at.desc()).all()

            return [
                {
                    "session_id": record.session_id,
                    "created_at": record.created_at,
                    "row_count": record.merged_row_count,
                    "status": record.status,
                }
                for record in records
            ]

        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        try:
            upload_record = self.db.query(UploadRecord).filter(
                UploadRecord.session_id == session_id
            ).first()

            if upload_record:
                self.db.delete(upload_record)
                self.db.commit()
                return True

            return False

        except Exception as e:
            self.db.rollback()
            print(f"Error deleting session: {e}")
            return False


def get_storage_manager() -> StorageManager:
    storage_mode = os.getenv("STORAGE_MODE", "session")

    if storage_mode == "persistent":
        return PersistentStorage()
    else:
        return SessionBasedStorage()

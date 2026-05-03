"""
SQLAlchemy ORM models for database tables.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    uploads = relationship("UploadRecord", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UploadRecord(Base):
    __tablename__ = "upload_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    po_row_count = Column(Integer, nullable=False)
    oc_row_count = Column(Integer, nullable=False)
    ship_row_count = Column(Integer, nullable=False)
    merged_row_count = Column(Integer, nullable=False)

    status = Column(String(20), default="completed")  # completed, processing, error
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    po_file_hash = Column(String(64), nullable=True)
    oc_file_hash = Column(String(64), nullable=True)
    ship_file_hash = Column(String(64), nullable=True)

    user = relationship("User", back_populates="uploads")
    processed_data = relationship("ProcessedData", back_populates="upload_record", uselist=False)
    bhm_results = relationship("BHMResult", back_populates="upload_record")


class ProcessedData(Base):

    __tablename__ = "processed_data"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_records.id"), unique=True, nullable=False)

    merged_data_json = Column(JSON, nullable=True)
    
    total_spending = Column(Float, nullable=False)
    average_transaction_value = Column(Float, nullable=False)
    vendor_count = Column(Integer, nullable=False)
    transaction_count = Column(Integer, nullable=False)

    price_discrepancy_mean = Column(Float, nullable=False)
    price_discrepancy_std = Column(Float, nullable=False)
    price_discrepancy_min = Column(Float, nullable=False)
    price_discrepancy_max = Column(Float, nullable=False)

    delay_mean = Column(Float, nullable=False)
    delay_std = Column(Float, nullable=False)
    delay_min = Column(Float, nullable=False)
    delay_max = Column(Float, nullable=False)

    computed_at = Column(DateTime, default=datetime.utcnow)

    upload_record = relationship("UploadRecord", back_populates="processed_data")
    vendor_metrics = relationship("VendorMetric", back_populates="processed_data")


class VendorMetric(Base):
    __tablename__ = "vendor_metrics"

    id = Column(Integer, primary_key=True, index=True)
    processed_data_id = Column(Integer, ForeignKey("processed_data.id"), nullable=False)
    
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_id = Column(String(255), nullable=True)

    transaction_count = Column(Integer, nullable=False)
    total_spending = Column(Float, nullable=False)
    average_spending = Column(Float, nullable=False)
    
    price_discrepancy_mean = Column(Float, nullable=False)
    price_discrepancy_std = Column(Float, nullable=False)
    
    delay_mean = Column(Float, nullable=False)
    delay_std = Column(Float, nullable=False)
    
    computed_at = Column(DateTime, default=datetime.utcnow)
 
    processed_data = relationship("ProcessedData", back_populates="vendor_metrics")


class BHMResult(Base):

    __tablename__ = "bhm_results"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_records.id"), nullable=False)
    
    model_version = Column(String(10), nullable=True)  # e.g., "2025", "2026"
    model_year = Column(Integer, nullable=True)

    mcmc_iterations = Column(Integer, default=2000)
    mcmc_chains = Column(Integer, default=4)
    mcmc_tuning = Column(Integer, default=1000)

    convergence_status = Column(String(20), default="not_evaluated")  # converged, not_converged, warnings
    convergence_warnings = Column(Text, nullable=True)  # JSON list of warnings

    fitted_at = Column(DateTime, default=datetime.utcnow)
    fitting_time_seconds = Column(Float, nullable=True)

    model_pickle = Column(JSON, nullable=True)

    upload_record = relationship("UploadRecord", back_populates="bhm_results")
    vendor_rankings = relationship("VendorRanking", back_populates="bhm_result")


class VendorRanking(Base):

    __tablename__ = "vendor_rankings"

    id = Column(Integer, primary_key=True, index=True)
    bhm_result_id = Column(Integer, ForeignKey("bhm_results.id"), nullable=False, index=True)
    
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_id = Column(String(255), nullable=True)

    price_accuracy_mean = Column(Float, nullable=False)
    price_accuracy_ci_lower = Column(Float, nullable=False)
    price_accuracy_ci_upper = Column(Float, nullable=False)

    timeliness_mean = Column(Float, nullable=False)
    timeliness_ci_lower = Column(Float, nullable=False)
    timeliness_ci_upper = Column(Float, nullable=False)

    combined_rank_score = Column(Float, nullable=False, index=True)  #Weighted average
    rank = Column(Integer, nullable=False, index=True)

    transaction_count = Column(Integer, nullable=False)
    confidence_level = Column(String(20), default="medium")  #high, medium, low

    computed_at = Column(DateTime, default=datetime.utcnow)

    bhm_result = relationship("BHMResult", back_populates="vendor_rankings")


class ModelCheckpoint(Base):
    __tablename__ = "model_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(10), unique=True, index=True, nullable=False)  # e.g., "2025"
    model_year = Column(Integer, unique=True, index=True, nullable=False)

    price_accuracy_posteriors = Column(JSON, nullable=False)
    timeliness_posteriors = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by_bhm_result_id = Column(Integer, nullable=True)
    
    vendor_count = Column(Integer, nullable=False)
    description = Column(Text, nullable=True) 
    is_locked = Column(Boolean, default=False)


class SessionData(Base):

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For session timeout

    storage_mode = Column(String(20), default="session")  # session or persistent
    status = Column(String(20), default="active")  # active, completed, expired

    current_upload_id = Column(Integer, ForeignKey("upload_records.id"), nullable=True)

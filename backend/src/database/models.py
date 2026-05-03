"""
SQLAlchemy ORM models for database tables.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.connection import Base


class User(Base):
    """
    User account for persistent data storage.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    uploads = relationship("UploadRecord", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UploadRecord(Base):
    """
    Records metadata for each data upload.
    Tracks PO, OC, and Ship file uploads.
    """
    __tablename__ = "upload_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Upload metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Data statistics
    po_row_count = Column(Integer, nullable=False)
    oc_row_count = Column(Integer, nullable=False)
    ship_row_count = Column(Integer, nullable=False)
    merged_row_count = Column(Integer, nullable=False)
    
    # Processing metadata
    status = Column(String(20), default="completed")  # completed, processing, error
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # File checksums or identifiers (optional, for validation)
    po_file_hash = Column(String(64), nullable=True)
    oc_file_hash = Column(String(64), nullable=True)
    ship_file_hash = Column(String(64), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="uploads")
    processed_data = relationship("ProcessedData", back_populates="upload_record", uselist=False)
    bhm_results = relationship("BHMResult", back_populates="upload_record")


class ProcessedData(Base):
    """
    Stores the merged and feature-engineered dataset.
    """
    __tablename__ = "processed_data"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_records.id"), unique=True, nullable=False)
    
    # Store merged data as JSON (for small datasets) or reference to external storage
    merged_data_json = Column(JSON, nullable=True)  # First N rows for preview
    
    # Global statistics
    total_spending = Column(Float, nullable=False)
    average_transaction_value = Column(Float, nullable=False)
    vendor_count = Column(Integer, nullable=False)
    transaction_count = Column(Integer, nullable=False)
    
    # Price discrepancy metrics
    price_discrepancy_mean = Column(Float, nullable=False)
    price_discrepancy_std = Column(Float, nullable=False)
    price_discrepancy_min = Column(Float, nullable=False)
    price_discrepancy_max = Column(Float, nullable=False)
    
    # Delay metrics
    delay_mean = Column(Float, nullable=False)
    delay_std = Column(Float, nullable=False)
    delay_min = Column(Float, nullable=False)
    delay_max = Column(Float, nullable=False)
    
    # Metadata
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    upload_record = relationship("UploadRecord", back_populates="processed_data")
    vendor_metrics = relationship("VendorMetric", back_populates="processed_data")


class VendorMetric(Base):
    """
    Pre-computed metrics for each vendor (from descriptive statistics).
    """
    __tablename__ = "vendor_metrics"

    id = Column(Integer, primary_key=True, index=True)
    processed_data_id = Column(Integer, ForeignKey("processed_data.id"), nullable=False)
    
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_id = Column(String(255), nullable=True)
    
    # Vendor statistics
    transaction_count = Column(Integer, nullable=False)
    total_spending = Column(Float, nullable=False)
    average_spending = Column(Float, nullable=False)
    
    price_discrepancy_mean = Column(Float, nullable=False)
    price_discrepancy_std = Column(Float, nullable=False)
    
    delay_mean = Column(Float, nullable=False)
    delay_std = Column(Float, nullable=False)
    
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    processed_data = relationship("ProcessedData", back_populates="vendor_metrics")


class BHMResult(Base):
    """
    Stores BHM model results for a session.
    Can be versioned (e.g., model_2025, model_2026) for yearly audits.
    """
    __tablename__ = "bhm_results"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_records.id"), nullable=False)
    
    # Model versioning for posterior-as-prior workflow
    model_version = Column(String(10), nullable=True)  # e.g., "2025", "2026"
    model_year = Column(Integer, nullable=True)
    
    # MCMC configuration
    mcmc_iterations = Column(Integer, default=2000)
    mcmc_chains = Column(Integer, default=4)
    mcmc_tuning = Column(Integer, default=1000)
    
    # Convergence diagnostics
    convergence_status = Column(String(20), default="not_evaluated")  # converged, not_converged, warnings
    convergence_warnings = Column(Text, nullable=True)  # JSON list of warnings
    
    # Model metadata
    fitted_at = Column(DateTime, default=datetime.utcnow)
    fitting_time_seconds = Column(Float, nullable=True)
    
    # Store model serialized object or reference (advanced)
    model_pickle = Column(JSON, nullable=True)  # Serialized posterior samples
    
    # Relationships
    upload_record = relationship("UploadRecord", back_populates="bhm_results")
    vendor_rankings = relationship("VendorRanking", back_populates="bhm_result")


class VendorRanking(Base):
    """
    Vendor rankings and BHM scores (one record per vendor per BHM run).
    """
    __tablename__ = "vendor_rankings"

    id = Column(Integer, primary_key=True, index=True)
    bhm_result_id = Column(Integer, ForeignKey("bhm_results.id"), nullable=False, index=True)
    
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_id = Column(String(255), nullable=True)
    
    # Price accuracy scores (from BHM posterior)
    price_accuracy_mean = Column(Float, nullable=False)
    price_accuracy_ci_lower = Column(Float, nullable=False)
    price_accuracy_ci_upper = Column(Float, nullable=False)
    
    # Timeliness scores (from BHM posterior)
    timeliness_mean = Column(Float, nullable=False)
    timeliness_ci_lower = Column(Float, nullable=False)
    timeliness_ci_upper = Column(Float, nullable=False)
    
    # Combined ranking
    combined_rank_score = Column(Float, nullable=False, index=True)  # Weighted average
    rank = Column(Integer, nullable=False, index=True)  # 1 = best, 2 = second, etc.
    
    # Data confidence
    transaction_count = Column(Integer, nullable=False)
    confidence_level = Column(String(20), default="medium")  # high, medium, low
    
    # Computed timestamp
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bhm_result = relationship("BHMResult", back_populates="vendor_rankings")


class ModelCheckpoint(Base):
    """
    Stores versioned model posteriors for year-over-year audits.
    Enables posterior-as-prior workflow for the next year's model.
    """
    __tablename__ = "model_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(10), unique=True, index=True, nullable=False)  # e.g., "2025"
    model_year = Column(Integer, unique=True, index=True, nullable=False)
    
    # Posterior samples or summary statistics
    price_accuracy_posteriors = Column(JSON, nullable=False)  # Dict of vendor -> posterior samples
    timeliness_posteriors = Column(JSON, nullable=False)      # Dict of vendor -> posterior samples
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by_bhm_result_id = Column(Integer, nullable=True)  # Link to BHMResult that generated it
    
    vendor_count = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)  # Audit notes
    is_locked = Column(Boolean, default=False)  # Lock to prevent accidental overwrites


class SessionData(Base):
    """
    Tracks active sessions (for session-based mode).
    Can also be used to track user sessions in persistent mode.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(String(255), nullable=True, index=True)
    
    # Session lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For session timeout
    
    # Session state
    storage_mode = Column(String(20), default="session")  # session or persistent
    status = Column(String(20), default="active")  # active, completed, expired
    
    # Data references
    current_upload_id = Column(Integer, ForeignKey("upload_records.id"), nullable=True)

"""
Pydantic models for API request/response schemas and data structures.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============================================================================
# Upload & Session Models
# ============================================================================

class UploadResponse(BaseModel):
    """Response after uploading PO, OC, and Ship datasets."""
    session_id: str = Field(..., description="Unique session identifier")
    status: int = Field(200, description="HTTP status code")
    message: str = Field("Upload successful", description="Status message")
    row_count: int = Field(..., description="Number of rows in merged dataset")
    columns: List[str] = Field(..., description="Column names in merged dataset")
    data_sample: Dict[str, Any] = Field(..., description="First row of merged data as dict")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-xyz789",
                "status": 200,
                "message": "Upload successful",
                "row_count": 150,
                "columns": ["po_number", "oc_number", "vendor_name", "price_discrepancy", "delay"],
                "data_sample": {"po_number": "PO-001", "vendor_name": "Vendor A"}
            }
        }


class UploadErrorResponse(BaseModel):
    """Error response for upload failures."""
    status: int = Field(400, description="HTTP status code")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


# ============================================================================
# Dashboard Models
# ============================================================================

class VendorStats(BaseModel):
    """Statistics for a single vendor."""
    vendor_name: str
    transaction_count: int
    total_spending: float = Field(..., description="Sum of all PO total_price")
    average_spending: float
    price_discrepancy_mean: float
    price_discrepancy_std: float
    delay_mean: float = Field(..., description="Average delay in days")
    delay_std: float


class DashboardMetrics(BaseModel):
    """Aggregated dashboard metrics."""
    session_id: str
    total_transactions: int
    total_spending: float
    average_transaction_value: float
    vendor_count: int
    price_discrepancy_mean: float
    price_discrepancy_std: float
    delay_mean: float
    delay_std: float
    vendors: List[VendorStats] = Field(..., description="Per-vendor statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-xyz789",
                "total_transactions": 150,
                "total_spending": 1500000.0,
                "average_transaction_value": 10000.0,
                "vendor_count": 5,
                "price_discrepancy_mean": 250.5,
                "price_discrepancy_std": 120.3,
                "delay_mean": 2.5,
                "delay_std": 3.2,
                "vendors": []
            }
        }


class TrendDataPoint(BaseModel):
    """Single data point for trend visualization."""
    date: str
    vendor_name: str
    value: float
    metric_type: str = Field(..., description="e.g., 'spending', 'price_discrepancy', 'delay'")


class VisualizationData(BaseModel):
    """Data structure for frontend visualization."""
    data_points: List[TrendDataPoint]
    metric_name: str
    unit: str = Field(..., description="e.g., 'USD', 'days', 'amount'")


# ============================================================================
# BHM Models
# ============================================================================

class VendorBHMScore(BaseModel):
    """BHM-derived vendor performance score."""
    vendor_name: str
    vendor_id: Optional[str] = None
    price_accuracy_score: float = Field(..., description="Posterior mean of price accuracy")
    price_accuracy_ci_lower: float = Field(..., description="95% credible interval lower bound")
    price_accuracy_ci_upper: float = Field(..., description="95% credible interval upper bound")
    timeliness_score: float = Field(..., description="Posterior mean of timeliness")
    timeliness_ci_lower: float
    timeliness_ci_upper: float
    combined_rank_score: float = Field(..., description="Weighted average: 0.5*accuracy + 0.5*timeliness")
    rank: int = Field(..., description="Overall vendor rank (1 = best)")
    transaction_count: int = Field(..., description="Number of transactions for this vendor")


class BHMRankingsResponse(BaseModel):
    """Response with vendor rankings from BHM."""
    session_id: str
    model_type: str = Field("Bayesian Hierarchical Model", description="Type of model used")
    convergence_status: str = Field(..., description="'converged' or 'not_converged'")
    convergence_warnings: List[str] = Field(default_factory=list, description="List of convergence issues if any")
    mcmc_iterations: int = Field(2000, description="Number of MCMC iterations performed")
    mcmc_chains: int = Field(4, description="Number of MCMC chains")
    rankings: List[VendorBHMScore] = Field(..., description="Sorted by combined_rank_score descending")
    model_timestamp: datetime = Field(..., description="When model was fit")
    posterior_version: Optional[str] = Field(None, description="e.g., '2025' or '2026' if using versioned priors")


class BHMDiagnostics(BaseModel):
    """MCMC convergence diagnostics."""
    metric_name: str
    r_hat: float = Field(..., description="Gelman-Rubin convergence statistic (should be < 1.01)")
    effective_sample_size: int
    has_divergences: bool
    rhat_status: str = Field(..., description="'good' if < 1.01, 'warning' if >= 1.01")


class BHMVendorDetailResponse(BaseModel):
    """Detailed BHM results for a single vendor."""
    session_id: str
    vendor_name: str
    vendor_id: Optional[str] = None
    combined_rank_score: float
    rank: int
    
    # Price accuracy metrics
    price_accuracy_mean: float
    price_accuracy_ci_lower: float
    price_accuracy_ci_upper: float
    price_accuracy_posterior_samples: Optional[List[float]] = Field(None, description="MCMC samples for posterior")
    
    # Timeliness metrics
    timeliness_mean: float
    timeliness_ci_lower: float
    timeliness_ci_upper: float
    timeliness_posterior_samples: Optional[List[float]] = Field(None, description="MCMC samples for posterior")
    
    # Diagnostics
    diagnostics: List[BHMDiagnostics]
    transaction_count: int
    confidence: str = Field(..., description="'high' if enough data, 'low' if sparse")


class ModelLockRequest(BaseModel):
    """Request to lock current model posteriors as prior for next year."""
    model_year: str = Field(..., description="e.g., '2025' or '2026'")
    description: Optional[str] = Field(None, description="Optional audit notes")


class ModelLockResponse(BaseModel):
    """Response after locking model."""
    status: str = Field("locked", description="Status of lock operation")
    model_year: str
    locked_at: datetime
    vendor_count: int
    summary: str


# ============================================================================
# Session & Storage Models
# ============================================================================

class SessionData(BaseModel):
    """Structure for storing session or persistent data."""
    session_id: str
    po_data: Optional[Dict[str, Any]] = None  # Simplified representation
    oc_data: Optional[Dict[str, Any]] = None
    ship_data: Optional[Dict[str, Any]] = None
    merged_data_row_count: int
    created_at: datetime
    last_accessed: datetime
    storage_mode: str = Field(..., description="'session' or 'persistent'")
    user_id: Optional[str] = Field(None, description="For persistent mode only")


class UploadHistory(BaseModel):
    """Record of past uploads (for persistent mode)."""
    session_id: str
    uploaded_at: datetime
    row_count: int
    vendor_count: int
    status: str = Field("completed", description="'completed', 'processing', 'error'")
    summary: Optional[str] = None


# ============================================================================
# Authentication Models
# ============================================================================

class UserRegister(BaseModel):
    """User registration request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="User's full name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """User login request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response after login/register."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User's full name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 1,
                "email": "user@example.com",
                "full_name": "John Doe"
            }
        }


class UserProfile(BaseModel):
    """User profile information."""
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(True, description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        from_attributes = True


class AuthErrorResponse(BaseModel):
    """Error response for auth failures."""
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials"
            }
        }

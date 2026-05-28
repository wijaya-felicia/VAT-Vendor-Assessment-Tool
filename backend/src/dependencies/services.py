from functools import lru_cache
from src.services.upload import UploadService
from src.services.dashboard import DashboardService
from src.services.bhm import BHMService
from src.services.data_storage import get_storage_manager, StorageManager
from src.services.auth import AuthService


@lru_cache
def get_upload_service() -> UploadService:
    return UploadService()


@lru_cache
def get_dashboard_service() -> DashboardService:
    return DashboardService()


@lru_cache
def get_bhm_service() -> BHMService:
    try:
        return BHMService(
            mcmc_iterations=8000,   # 8000 iterations for better convergence
            mcmc_chains=8,          # 8 chains for robust sampling
            mcmc_tuning=2000,       # 2000 tuning steps
        )
    except ImportError as e:
        raise ImportError(f"BHM service requires PyMC: {e}")


@lru_cache
def get_storage_manager_cached() -> StorageManager:
    return get_storage_manager()


def get_auth_service() -> AuthService:
    """Get auth service instance."""
    return AuthService()
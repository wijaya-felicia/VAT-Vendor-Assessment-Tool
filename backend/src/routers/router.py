from fastapi import APIRouter
from src.routers.upload import upload_router
from src.routers.dashboard import dashboard_router
from src.routers.bhm import bhm_router
from src.routers.auth import auth_router

api = APIRouter()

api.include_router(auth_router, tags=["Authentication"])
api.include_router(upload_router, tags=["Upload"])
api.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api.include_router(bhm_router, prefix="/bhm", tags=["BHM"])
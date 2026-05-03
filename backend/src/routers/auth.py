from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.services.auth import AuthService
from src.types.models import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserProfile,
    AuthErrorResponse,
)
from src.dependencies.auth import get_current_user
from src.database.models import User


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": AuthErrorResponse, "description": "Email already registered or invalid data"},
        422: {"description": "Validation error"},
    },
)
async def register(user_data: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:

    try:
        token_response = AuthService.register_user(db, user_data)
        return token_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
async def login(credentials: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:

    try:
        token_response = AuthService.login_user(db, credentials.email, credentials.password)
        return token_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@auth_router.get(
    "/profile",
    response_model=UserProfile,
    responses={
        401: {"model": AuthErrorResponse, "description": "Unauthorized"},
    },
)
async def get_profile(current_user: User = Depends(get_current_user)) -> UserProfile:

    return AuthService.get_user_profile(current_user)


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Unauthorized"},
    },
)
async def refresh_token(current_user: User = Depends(get_current_user)) -> TokenResponse:

    token_data = {"sub": str(current_user.id), "email": current_user.email}
    access_token = AuthService.create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
    )

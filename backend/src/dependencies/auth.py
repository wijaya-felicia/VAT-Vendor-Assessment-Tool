"""
Authentication dependency functions for FastAPI.
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.services.auth import AuthService
from src.database.models import User
from typing import Optional


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token in Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer <token>)
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = AuthService.get_user_by_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_optional_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise None (for guest mode).
    
    Args:
        db: Database session
        authorization: Authorization header value (optional)
        
    Returns:
        User object if token is valid, None for guest access
    """
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None
    
    user = AuthService.get_user_by_token(db, token)
    return user


async def get_optional_user_from_header(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Extract user from Authorization header if present.
    
    Args:
        authorization: Authorization header value
        db: Database session
        
    Returns:
        User object if valid token provided, None otherwise
    """
    if not authorization:
        return None
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None
    
    user = AuthService.get_user_by_token(db, token)
    return user

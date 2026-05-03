"""
Authentication service for user registration, login, and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
import os
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.models import User
from src.types.models import UserRegister, TokenResponse, UserProfile


# JWT configuration - using environment variables with fallbacks
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # Default 24 hours


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Dictionary with claims to encode (typically user_id, email)
            expires_delta: Optional timedelta for token expiration
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token and return its claims.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary with token claims if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def register_user(
        db: Session,
        user_data: UserRegister,
    ) -> TokenResponse:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            TokenResponse with access token and user info
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError(f"Email {user_data.email} already registered")

        # Create new user
        hashed_password = AuthService.hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
        )

        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Email {user_data.email} already registered")

        # Create access token
        token_data = {"sub": str(new_user.id), "email": new_user.email}
        access_token = AuthService.create_access_token(token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
        )

    @staticmethod
    def login_user(db: Session, email: str, password: str) -> TokenResponse:
        """
        Authenticate a user and return a JWT token.
        
        Args:
            db: Database session
            email: User email
            password: User password
            
        Returns:
            TokenResponse with access token and user info
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")

        # Create access token
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = AuthService.create_access_token(token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
        )

    @staticmethod
    def get_user_by_token(db: Session, token: str) -> Optional[User]:
        """
        Get user from a valid JWT token.
        
        Args:
            db: Database session
            token: JWT token string
            
        Returns:
            User object if token is valid, None otherwise
        """
        payload = AuthService.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_user_profile(user: User) -> UserProfile:
        """
        Get user profile information.
        
        Args:
            user: User object
            
        Returns:
            UserProfile with user information
        """
        return UserProfile(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )

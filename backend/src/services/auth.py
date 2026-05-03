from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
import os
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.models import User
from src.types.models import UserRegister, TokenResponse, UserProfile

SECRET_KEY = os.getenv("SECRET_KEY", "helpmeivebecomeacorporateslaveinchubblifeGRAHH")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # Default 24 hours


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
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

        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError(f"Email {user_data.email} already registered")

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

        user = db.query(User).filter(User.email == email).first()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")

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

        return UserProfile(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )

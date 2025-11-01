"""
JWT authentication and security utilities.

Using python-jose for JWT handling.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData

# OAuth2 password bearer - FastAPI's way of handling JWT in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    # set expiry
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    # TODO: add jti for logout/blacklist?
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """
    Verify and decode JWT token.
    
    Returns TokenData with user information.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        tenant_id: Optional[int] = payload.get("tenant_id")
        role: Optional[str] = payload.get("role")
        username: Optional[str] = payload.get("username")
        
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            username=username
        )
        return token_data
    except JWTError:
        raise credentials_exception


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # verify token first
    token_data = verify_token(token, credentials_exception)
    
    # fetch user
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception  # token valid but user deleted? weird case
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


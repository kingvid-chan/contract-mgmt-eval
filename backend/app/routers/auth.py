"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.audit import AuditLogger
from app.models import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserInfoResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    MessageResponse,
)
from app.services import auth_service
from app.utils.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserInfoResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db), audit: AuditLogger = Depends()):
    """Register a new user account."""
    try:
        user = auth_service.register(db, body, ip_address=audit.ip_address)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db), audit: AuditLogger = Depends()):
    """Login with username and password, return JWT token."""
    try:
        result = auth_service.login(db, body.username, body.password, ip_address=audit.ip_address)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditLogger = Depends(),
):
    """Logout. Client should discard the token."""
    log_action(db, current_user.id, "user.logout", "user", current_user.id,
               f"User {current_user.username} logged out", ip_address=audit.ip_address)
    return {"message": "已登出"}


@router.get("/me", response_model=UserInfoResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.post("/password-reset", response_model=PasswordResetResponse)
def password_reset(body: PasswordResetRequest, db: Session = Depends(get_db), audit: AuditLogger = Depends()):
    """Request a password reset by email."""
    try:
        result = auth_service.reset_password(db, body.email, ip_address=audit.ip_address)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

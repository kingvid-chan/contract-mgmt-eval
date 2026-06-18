"""Authentication business logic."""

import secrets

from sqlalchemy.orm import Session

from app.models import User
from app.schemas.auth import RegisterRequest
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.audit import log_action


def register(db: Session, data: RegisterRequest) -> User:
    """Register a new user. Default role is 'user'."""
    # Check uniqueness
    if db.query(User).filter(User.username == data.username).first():
        raise ValueError("用户名已存在")
    if db.query(User).filter(User.email == data.email).first():
        raise ValueError("邮箱已被注册")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="user",
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, user.id, "user.register", "user", user.id)
    return user


def login(db: Session, username: str, password: str) -> dict:
    """Authenticate user and return JWT token.

    Raises ValueError if credentials are invalid or user is disabled.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("用户名或密码错误")

    if user.status == "disabled":
        raise ValueError("账户已被禁用")

    token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role}
    )

    log_action(db, user.id, "user.login", "user", user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
        },
    }


def reset_password(db: Session, email: str) -> dict:
    """Reset password for the given email.

    In this demo version, generates a new random password and returns it directly.
    Production should send an email with a reset link.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("该邮箱未注册")

    new_password = secrets.token_urlsafe(8)
    user.password_hash = hash_password(new_password)
    db.commit()

    log_action(db, user.id, "user.password_reset", "user", user.id)
    return {"message": "密码已重置", "new_password": new_password}

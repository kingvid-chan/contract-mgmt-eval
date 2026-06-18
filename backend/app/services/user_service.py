"""User management business logic."""

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password
from app.utils.audit import log_action


def list_users(
    db: Session,
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """List users with optional filtering and pagination."""
    query = db.query(User)

    if search:
        term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(term)) | (User.email.ilike(term))
        )
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    total = query.count()
    items = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"total": total, "items": items}


def create_user(db: Session, data: UserCreate, admin_id: int, ip_address: str | None = None) -> User:
    """Create a new user (admin only)."""
    if db.query(User).filter(User.username == data.username).first():
        raise ValueError("用户名已存在")
    if db.query(User).filter(User.email == data.email).first():
        raise ValueError("邮箱已被注册")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, admin_id, "user.create", "user", user.id,
               f"Created user {user.username} with role {user.role}", ip_address=ip_address)
    return user


def get_user(db: Session, user_id: int) -> User:
    """Get a single user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, admin_id: int, ip_address: str | None = None) -> User:
    """Update user fields. Only updates fields that are provided."""
    user = get_user(db, user_id)

    if data.username is not None and data.username != user.username:
        if db.query(User).filter(User.username == data.username).first():
            raise ValueError("用户名已存在")
        user.username = data.username

    if data.email is not None and data.email != user.email:
        if db.query(User).filter(User.email == data.email).first():
            raise ValueError("邮箱已被注册")
        user.email = data.email

    if data.password is not None:
        user.password_hash = hash_password(data.password)

    if data.role is not None:
        user.role = data.role

    db.commit()
    db.refresh(user)

    log_action(db, admin_id, "user.update", "user", user.id,
               f"Updated user {user.username}", ip_address=ip_address)
    return user


def toggle_user_status(db: Session, user_id: int, status: str, admin_id: int, ip_address: str | None = None) -> User:
    """Enable or disable a user."""
    user = get_user(db, user_id)

    if user.id == admin_id:
        raise ValueError("不能修改自己的账户状态")

    user.status = status
    db.commit()
    db.refresh(user)

    log_action(db, admin_id, "user.status_change", "user", user.id,
               f"Set user {user.username} status to {status}", ip_address=ip_address)
    return user

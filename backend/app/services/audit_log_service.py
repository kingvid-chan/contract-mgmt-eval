"""Audit log query service — read-only access to audit_logs with filters and pagination."""

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import AuditLog, User


def list_audit_logs(
    db: Session,
    action: str | None = None,
    user_search: str | None = None,
    user_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Query audit logs with optional filters, JOIN users for username.

    Filters:
      - action: exact match on action string
      - user_search: fuzzy match on username (LIKE %search%)
      - user_id: exact match on user_id (takes precedence over user_search)
      - start_date / end_date: filter by created_at range
    """
    # Base query with JOIN to get username
    query = (
        db.query(AuditLog, User.username)
        .join(User, AuditLog.user_id == User.id)
    )

    # Filters
    if action:
        query = query.filter(AuditLog.action == action)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    elif user_search:
        query = query.filter(User.username.ilike(f"%{user_search}%"))

    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    # Total count before pagination
    total = query.count()

    # Sort and paginate
    query = query.order_by(desc(AuditLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    rows = query.all()

    # Build response items
    items = []
    for audit_log, username in rows:
        items.append({
            "id": audit_log.id,
            "user_id": audit_log.user_id,
            "username": username,
            "action": audit_log.action,
            "target_type": audit_log.target_type,
            "target_id": audit_log.target_id,
            "detail": audit_log.detail,
            "ip_address": audit_log.ip_address,
            "created_at": audit_log.created_at,
        })

    return {"total": total, "items": items}

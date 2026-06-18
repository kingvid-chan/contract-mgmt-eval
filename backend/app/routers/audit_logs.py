"""Audit log API endpoints — read-only, admin only."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_admin
from app.schemas.audit_log import AuditLogListResponse
from app.services import audit_log_service

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    action: str | None = Query(None, description="按操作类型筛选"),
    user_search: str | None = Query(None, description="按用户名模糊搜索"),
    user_id: int | None = Query(None, description="按用户 ID 精确筛选"),
    start_date: str | None = Query(None, description="起始时间 ISO 格式"),
    end_date: str | None = Query(None, description="结束时间 ISO 格式"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user=Depends(require_admin),
):
    """List audit logs with optional filtering and pagination. Admin only.

    Filters:
      - action: exact match on action type
      - user_search: fuzzy match on username (ignored if user_id is set)
      - user_id: exact match on user ID
      - start_date / end_date: ISO 8601 datetime range
    """
    # Parse date strings
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
    if end_date:
        end_dt = datetime.fromisoformat(end_date)

    return audit_log_service.list_audit_logs(
        db=db,
        action=action,
        user_search=user_search,
        user_id=user_id,
        start_date=start_dt,
        end_date=end_dt,
        page=page,
        page_size=page_size,
    )

"""Contract template management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.middleware.audit import AuditLogger
from app.models import User
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateDropdownItem,
)
from app.services import template_service

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/dropdown", response_model=list[TemplateDropdownItem])
def list_templates_dropdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List non-deleted templates for dropdown (all authenticated users)."""
    return template_service.list_templates_dropdown(db)


@router.get("", response_model=TemplateListResponse)
def list_templates(
    search: str | None = Query(None, description="搜索模板名称/分类"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _admin: User = Depends(require_admin),
):
    """List templates with search, pagination (admin only)."""
    return template_service.list_templates(db, search, page, page_size, sort_by, sort_order)


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    body: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _admin: User = Depends(require_admin),
    audit: AuditLogger = Depends(),
):
    """Create a new template (admin only)."""
    template = template_service.create_template(
        db, body, current_user.id, ip_address=audit.ip_address
    )
    return template_service._to_response(template)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _admin: User = Depends(require_admin),
):
    """Get template detail (admin only)."""
    try:
        return template_service.get_template(db, template_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _admin: User = Depends(require_admin),
    audit: AuditLogger = Depends(),
):
    """Update template (admin only)."""
    try:
        return template_service.update_template(
            db, template_id, body, current_user.id, ip_address=audit.ip_address
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _admin: User = Depends(require_admin),
    audit: AuditLogger = Depends(),
):
    """Soft-delete a template (admin only)."""
    try:
        template_service.soft_delete_template(
            db, template_id, current_user.id, ip_address=audit.ip_address
        )
        return {"message": "模板已删除"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

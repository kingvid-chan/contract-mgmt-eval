"""Contract template management business logic."""

import re

from sqlalchemy.orm import Session

from app.models import ContractTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate
from app.utils.audit import log_action


PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def _to_response(template: ContractTemplate) -> dict:
    """Convert a ContractTemplate ORM object to a dict with extra fields."""
    return {
        "id": template.id,
        "name": template.name,
        "category": template.category,
        "party_a_default": template.party_a_default,
        "party_b_default": template.party_b_default,
        "content": template.content,
        "amount_min": template.amount_min,
        "amount_max": template.amount_max,
        "is_deleted": template.is_deleted,
        "created_by": template.created_by,
        "creator_username": template.creator.username if template.creator else None,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }


def _to_dropdown_item(template: ContractTemplate) -> dict:
    """Convert a template to a dropdown item."""
    return {
        "id": template.id,
        "name": template.name,
        "category": template.category,
    }


def list_templates(
    db: Session,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
) -> dict:
    """List non-deleted templates with search, pagination."""
    query = db.query(ContractTemplate).filter(ContractTemplate.is_deleted == False)

    if search:
        term = f"%{search}%"
        query = query.filter(
            (ContractTemplate.name.ilike(term))
            | (ContractTemplate.category.ilike(term))
        )

    sort_col = getattr(ContractTemplate, sort_by, ContractTemplate.updated_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "items": [_to_response(t) for t in items]}


def list_templates_dropdown(db: Session) -> list[dict]:
    """List non-deleted templates for the dropdown (all authenticated users)."""
    templates = (
        db.query(ContractTemplate)
        .filter(ContractTemplate.is_deleted == False)
        .order_by(ContractTemplate.name.asc())
        .all()
    )
    return [_to_dropdown_item(t) for t in templates]


def create_template(
    db: Session, data: TemplateCreate, user_id: int, ip_address: str | None = None
) -> ContractTemplate:
    """Create a new contract template."""
    template = ContractTemplate(
        name=data.name,
        category=data.category or "",
        party_a_default=data.party_a_default,
        party_b_default=data.party_b_default,
        content=data.content or "",
        amount_min=data.amount_min,
        amount_max=data.amount_max,
        created_by=user_id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    log_action(
        db, user_id, "template.create", "template", template.id,
        f"Created template '{template.name}'", ip_address=ip_address,
    )
    return template


def get_template(db: Session, template_id: int) -> dict:
    """Get a single template (non-deleted only)."""
    template = (
        db.query(ContractTemplate)
        .filter(ContractTemplate.id == template_id, ContractTemplate.is_deleted == False)
        .first()
    )
    if not template:
        raise ValueError("模板不存在")
    return _to_response(template)


def update_template(
    db: Session, template_id: int, data: TemplateUpdate, user_id: int, ip_address: str | None = None
) -> dict:
    """Update template fields."""
    template = (
        db.query(ContractTemplate)
        .filter(ContractTemplate.id == template_id, ContractTemplate.is_deleted == False)
        .first()
    )
    if not template:
        raise ValueError("模板不存在")

    if data.name is not None:
        template.name = data.name
    if data.category is not None:
        template.category = data.category
    if data.party_a_default is not None:
        template.party_a_default = data.party_a_default
    if data.party_b_default is not None:
        template.party_b_default = data.party_b_default
    if data.content is not None:
        template.content = data.content
    if data.amount_min is not None:
        template.amount_min = data.amount_min
    if data.amount_max is not None:
        template.amount_max = data.amount_max

    db.commit()
    db.refresh(template)

    log_action(
        db, user_id, "template.update", "template", template.id,
        f"Updated template '{template.name}'", ip_address=ip_address,
    )
    return _to_response(template)


def soft_delete_template(
    db: Session, template_id: int, user_id: int, ip_address: str | None = None
) -> None:
    """Soft-delete a template by setting is_deleted=True."""
    template = (
        db.query(ContractTemplate)
        .filter(ContractTemplate.id == template_id, ContractTemplate.is_deleted == False)
        .first()
    )
    if not template:
        raise ValueError("模板不存在")

    template.is_deleted = True
    db.commit()

    log_action(
        db, user_id, "template.delete", "template", template_id,
        f"Soft-deleted template '{template.name}'", ip_address=ip_address,
    )


def render_template_content(content: str, variables: dict[str, str]) -> str:
    """Replace {{variable}} placeholders in content with actual values.

    Args:
        content: Template content with {{placeholders}}.
        variables: Dict mapping placeholder names to replacement values.

    Returns:
        Content with all placeholders replaced.
    """
    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return variables.get(var_name, match.group(0))

    return PLACEHOLDER_RE.sub(replacer, content)

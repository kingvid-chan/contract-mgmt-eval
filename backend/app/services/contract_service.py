"""Contract management business logic."""

from datetime import date

from sqlalchemy.orm import Session

from app.models import Contract, User, Attachment
from app.schemas.contract import ContractCreate, ContractUpdate
from app.utils.audit import log_action


VALID_TRANSITIONS = {
    "draft": ["active"],
    "active": ["terminated", "expired"],
    "terminated": [],
    "expired": [],
}


def _check_ownership(db: Session, contract: Contract, user: User):
    """Raise ValueError if user is not admin and doesn't own the contract."""
    if user.role != "admin" and contract.created_by != user.id:
        raise ValueError("无权操作此合同")


def _to_response(contract: Contract) -> dict:
    """Convert a Contract ORM object to a dict with extra fields."""
    return {
        "id": contract.id,
        "title": contract.title,
        "contract_no": contract.contract_no,
        "party_a": contract.party_a,
        "party_b": contract.party_b,
        "amount": contract.amount,
        "status": contract.status,
        "sign_date": contract.sign_date,
        "expiry_date": contract.expiry_date,
        "content": contract.content,
        "created_by": contract.created_by,
        "creator_username": contract.creator.username if contract.creator else None,
        "attachment_count": len(contract.attachments) if contract.attachments else 0,
        "created_at": contract.created_at,
        "updated_at": contract.updated_at,
    }


def list_contracts(
    db: Session,
    user: User,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "id",
    sort_order: str = "desc",
) -> dict:
    """List contracts with search, filter, pagination."""
    query = db.query(Contract)

    # Non-admin users only see their own contracts
    if user.role != "admin":
        query = query.filter(Contract.created_by == user.id)

    if search:
        term = f"%{search}%"
        query = query.filter(
            (Contract.title.ilike(term))
            | (Contract.contract_no.ilike(term))
            | (Contract.party_a.ilike(term))
            | (Contract.party_b.ilike(term))
        )
    if status:
        query = query.filter(Contract.status == status)

    # Sort
    sort_col = getattr(Contract, sort_by, Contract.id)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "items": [_to_response(c) for c in items]}


def create_contract(db: Session, data: ContractCreate, user: User, ip_address: str | None = None) -> Contract:
    """Create a new contract with draft status."""
    if db.query(Contract).filter(Contract.contract_no == data.contract_no).first():
        raise ValueError("合同编号已存在")

    contract = Contract(
        title=data.title,
        contract_no=data.contract_no,
        party_a=data.party_a,
        party_b=data.party_b,
        amount=data.amount or 0.0,
        status="draft",
        sign_date=data.sign_date,
        expiry_date=data.expiry_date,
        content=data.content or "",
        created_by=user.id,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    log_action(db, user.id, "contract.create", "contract", contract.id,
               f"Created contract {contract.contract_no}", ip_address=ip_address)
    return contract


def get_contract(db: Session, contract_id: int, user: User) -> dict:
    """Get a single contract with ownership check."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    _check_ownership(db, contract, user)
    return _to_response(contract)


def update_contract(db: Session, contract_id: int, data: ContractUpdate, user: User, ip_address: str | None = None) -> dict:
    """Update contract fields."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    _check_ownership(db, contract, user)

    if data.title is not None:
        contract.title = data.title
    if data.contract_no is not None and data.contract_no != contract.contract_no:
        if db.query(Contract).filter(Contract.contract_no == data.contract_no).first():
            raise ValueError("合同编号已存在")
        contract.contract_no = data.contract_no
    if data.party_a is not None:
        contract.party_a = data.party_a
    if data.party_b is not None:
        contract.party_b = data.party_b
    if data.amount is not None:
        contract.amount = data.amount
    if data.sign_date is not None:
        contract.sign_date = data.sign_date
    if data.expiry_date is not None:
        contract.expiry_date = data.expiry_date
    if data.content is not None:
        contract.content = data.content

    db.commit()
    db.refresh(contract)

    log_action(db, user.id, "contract.update", "contract", contract.id,
               f"Updated contract {contract.contract_no}", ip_address=ip_address)
    return _to_response(contract)


def delete_contract(db: Session, contract_id: int, user: User, ip_address: str | None = None) -> None:
    """Delete a contract. Only draft status can be deleted."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    _check_ownership(db, contract, user)

    if contract.status != "draft":
        raise ValueError("只有草稿状态的合同可以删除")

    db.delete(contract)
    db.commit()

    log_action(db, user.id, "contract.delete", "contract", contract_id,
               f"Deleted contract {contract.contract_no}", ip_address=ip_address)


def update_contract_status(
    db: Session, contract_id: int, new_status: str, user: User, ip_address: str | None = None
) -> dict:
    """Transition contract to a new status with validation."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    _check_ownership(db, contract, user)

    allowed = VALID_TRANSITIONS.get(contract.status, [])
    if new_status not in allowed:
        raise ValueError(f"不允许从 {contract.status} 流转到 {new_status}")

    if new_status == "active" and not contract.sign_date:
        contract.sign_date = date.today()

    contract.status = new_status
    db.commit()
    db.refresh(contract)

    log_action(db, user.id, "contract.status_change", "contract", contract.id,
               f"Changed contract {contract.contract_no} status: {contract.status} → {new_status}",
               ip_address=ip_address)
    return _to_response(contract)

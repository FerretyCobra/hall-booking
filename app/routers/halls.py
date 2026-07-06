"""IT hall management. Rename is safe because bookings reference hall_id, not
the name. 'Delete' is a soft archive so historical bookings keep their hall."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db, transaction
from ..models import Hall, User
from ..schemas import HallIn, HallPatch, HallOut
from ..security import require_admin
from ..services import audit

router = APIRouter(prefix="/api/admin/halls", tags=["admin:halls"])


@router.get("", response_model=list[HallOut])
def list_all(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return db.query(Hall).order_by(Hall.name).all()


@router.post("", response_model=HallOut)
def create(payload: HallIn, request: Request,
           db: Session = Depends(get_db), user: User = Depends(require_admin)):
    with transaction(db):
        hall = Hall(name=payload.name.strip(), capacity=payload.capacity)
        db.add(hall)
        db.flush()
        audit.log(db, "hall.create", entity="hall", entity_id=hall.id,
                  actor=user.username, actor_ip=request.client.host, detail=hall.name)
    return hall


@router.patch("/{hall_id}", response_model=HallOut)
def update(hall_id: int, payload: HallPatch, request: Request,
           db: Session = Depends(get_db), user: User = Depends(require_admin)):
    with transaction(db):
        hall = db.get(Hall, hall_id)
        if not hall:
            raise HTTPException(404, "Hall not found.")
        if payload.name is not None:
            hall.name = payload.name.strip()
        if payload.capacity is not None:
            hall.capacity = payload.capacity
        if payload.active is not None:
            hall.active = payload.active
        audit.log(db, "hall.update", entity="hall", entity_id=hall.id,
                  actor=user.username, actor_ip=request.client.host,
                  detail=payload.model_dump(exclude_none=True).__str__())
    return hall

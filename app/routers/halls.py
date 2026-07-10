"""IT hall management. Rename is safe because bookings reference hall_id, not
the name. 'Delete' is a soft archive so historical bookings keep their hall."""
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
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
        hall = Hall(name=payload.name.strip(), capacity=payload.capacity, image=payload.image)
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
        if payload.image is not None:
            hall.image = payload.image
        if payload.active is not None:
            hall.active = payload.active
        audit.log(db, "hall.update", entity="hall", entity_id=hall.id,
                  actor=user.username, actor_ip=request.client.host,
                  detail=payload.model_dump(exclude_none=True).__str__())
    return hall


@router.post("/{hall_id}/picture", response_model=HallOut)
def upload_picture(hall_id: int, request: Request, file: UploadFile = File(...),
                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    hall = db.get(Hall, hall_id)
    if not hall:
        raise HTTPException(404, "Hall not found.")
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Uploaded file must be an image.")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        ext = ".png"
        
    filename = f"hall_{hall_id}{ext}"
    
    from ..config import BASE_DIR
    static_images_dir = BASE_DIR / "static" / "images"
    static_images_dir.mkdir(exist_ok=True, parents=True)
    
    dest_path = static_images_dir / filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    with transaction(db):
        hall.image = filename
        audit.log(db, "hall.update_picture", entity="hall", entity_id=hall.id,
                  actor=user.username, actor_ip=request.client.host,
                  detail=f"Uploaded image: {filename}")
    return hall

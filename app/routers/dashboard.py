from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Booking, Hall, AuditLog, User, DropdownConfig
from ..schemas import DropdownConfigIn
from ..security import require_admin
from ..services import audit

router = APIRouter(prefix="/api/admin", tags=["admin:dashboard"])


@router.get("/bookings")
def bookings(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    on: date | None = Query(None, description="Filter to a single date"),
    status: str | None = Query(None),
):
    """All bookings across halls; the dashboard polls this for the live view."""
    q = db.query(Booking, Hall).join(Hall, Booking.hall_id == Hall.id)
    if on:
        q = q.filter(Booking.booking_date == on)
    if status:
        q = q.filter(Booking.status == status)
    rows = q.order_by(Booking.booking_date.desc(), Booking.start_time).all()
    return [
        {
            "id": b.id, "hall": h.name, "hall_id": h.id,
            "date": b.booking_date.isoformat(),
            "start": b.start_time, "end": b.end_time,
            "booked_by": b.booked_by, "dept": b.dept, "purpose": b.purpose,
            "status": b.status, "created_ip": b.created_ip,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "support_staff_requested": b.support_staff_requested,
            "housekeeping_requested": b.housekeeping_requested,
            "scientist_designation": b.scientist_designation,
            "project_id": b.project_id,
            "attendees_count": b.attendees_count,
            "features_requested": b.features_requested,
            "cancel_code": b.cancel_code,
            "coordinator_name": b.coordinator_name,
            "coordinator_phone": b.coordinator_phone,
            "virtual_meeting_requested": b.virtual_meeting_requested,
            "meeting_link": b.meeting_link,
            "stationery_requested": b.stationery_requested,
            "food_requested": b.food_requested,
        }
        for b, h in rows
    ]


@router.post("/bookings/{booking_id}/approve")
def approve_booking(booking_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.meetings import get_active_meeting_provider
    from ..services.notifications import send_booking_confirmation
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found.")
    if booking.status != "pending_approval":
        raise HTTPException(400, f"Booking status is {booking.status}, cannot approve.")
    
    booking.status = "confirmed"
    
    # Generate meeting link if requested
    if booking.virtual_meeting_requested and not booking.meeting_link:
        provider = get_active_meeting_provider()
        booking.meeting_link = provider.create_meeting(booking.id, booking.purpose or "Meeting")
        
    db.commit()
    
    hall = db.get(Hall, booking.hall_id)
    try:
        send_booking_confirmation(db, booking, hall)
    except Exception as e:
        print(f"Error sending booking confirmation email: {e}")

    audit.log(db, "booking.approve", entity="booking", entity_id=booking.id,
              actor=user.username, detail=f"Approved booking {booking.id}")
    return {"status": "confirmed", "meeting_link": booking.meeting_link}


@router.post("/bookings/{booking_id}/reject")
def reject_booking(booking_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.notifications import send_booking_rejection
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found.")
    if booking.status != "pending_approval":
        raise HTTPException(400, f"Booking status is {booking.status}, cannot reject.")
    
    booking.status = "cancelled"
    db.commit()

    hall = db.get(Hall, booking.hall_id)
    try:
        send_booking_rejection(db, booking, hall)
    except Exception as e:
        print(f"Error sending booking rejection email: {e}")

    audit.log(db, "booking.reject", entity="booking", entity_id=booking.id,
              actor=user.username, detail=f"Rejected booking {booking.id}")
    return {"status": "cancelled"}


@router.get("/dropdowns")
def list_dropdowns(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return db.query(DropdownConfig).all()


@router.post("/dropdowns")
def create_dropdown(payload: DropdownConfigIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    item = DropdownConfig(category=payload.category, value=payload.value)
    db.add(item)
    db.commit()
    db.refresh(item)
    audit.log(db, "dropdown.create", entity="dropdown_configs", entity_id=item.id,
              actor=user.username, detail=f"Created dropdown {item.category}: {item.value}")
    return item


@router.delete("/dropdowns/{item_id}")
def delete_dropdown(item_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    item = db.get(DropdownConfig, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    audit.log(db, "dropdown.delete", entity="dropdown_configs", entity_id=item_id,
              actor=user.username, detail=f"Deleted dropdown {item.category}: {item.value}")
    return {"status": "deleted"}


@router.post("/trigger-notifications")
def trigger_notifications(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.notifications import send_department_notifications
    try:
        send_department_notifications(db)
        return {"status": "success", "message": "Notifications sent"}
    except Exception as e:
        raise HTTPException(500, f"Notification trigger failed: {str(e)}")


@router.get("/audit")
def audit_log(db: Session = Depends(get_db), user: User = Depends(require_admin),
              limit: int = Query(100, le=500)):
    rows = db.query(AuditLog).order_by(AuditLog.ts.desc()).limit(limit).all()
    return [
        {"id": r.id, "action": r.action, "entity": r.entity, "entity_id": r.entity_id,
         "actor": r.actor, "actor_ip": r.actor_ip, "detail": r.detail,
         "ts": r.ts.isoformat() if r.ts else None}
        for r in rows
    ]


@router.get("/settings")
def get_system_settings(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.settings import get_all_settings
    return get_all_settings(db)


@router.post("/settings")
def update_system_settings(payload: dict, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    from ..services.settings import save_settings
    save_settings(db, payload)
    audit.log(db, "settings.update", entity="settings", actor=user.username)
    return {"status": "success"}

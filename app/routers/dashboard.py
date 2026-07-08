"""IT dashboard reads: the live bookings feed (polled) and the audit trail."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Booking, Hall, AuditLog, User
from ..security import require_admin

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
            "scientist_designation": b.scientist_designation,
            "project_id": b.project_id,
            "attendees_count": b.attendees_count,
            "features_requested": b.features_requested,
        }
        for b, h in rows
    ]


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

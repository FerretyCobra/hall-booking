"""Public booking API. No login: bookers just supply a name/dept."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from ..config import DAY_START, DAY_END, SLOT_MINUTES
from ..database import get_db
from ..models import Hall, HallFeature, Booking, FeatureCatalog, FeatureOption
from ..schemas import BookingIn, CancelIn
from ..services import bookings as booking_svc

router = APIRouter(prefix="/api", tags=["public"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _hall_feature_summary(db: Session, hall_id: int):
    """Human-readable feature list for a hall, e.g. 'Microphone: handheld x2'."""
    rows = (
        db.query(HallFeature, FeatureCatalog, FeatureOption)
        .join(FeatureCatalog, HallFeature.feature_id == FeatureCatalog.id)
        .outerjoin(FeatureOption, HallFeature.option_id == FeatureOption.id)
        .filter(HallFeature.hall_id == hall_id, FeatureCatalog.active == True)  # noqa: E712
        .all()
    )
    out = []
    for hf, feat, opt in rows:
        label = feat.name
        if opt:
            label += f": {opt.label}"
        elif hf.value:
            label += f": {hf.value}"
        if hf.quantity:
            label += f" x{hf.quantity}"
        out.append(label)
    return out


@router.get("/config")
def ui_config():
    return {"day_start": DAY_START, "day_end": DAY_END, "slot_minutes": SLOT_MINUTES}


@router.get("/halls")
def list_halls(
    db: Session = Depends(get_db),
    min_capacity: int = Query(0, ge=0),
    feature_id: int | None = None,
    option_id: int | None = None,
):
    """Active halls, optionally filtered by capacity and a required feature/option."""
    q = db.query(Hall).filter(Hall.active == True)  # noqa: E712
    if min_capacity:
        q = q.filter(Hall.capacity >= min_capacity)
    halls = q.order_by(Hall.name).all()

    if feature_id or option_id:
        keep = []
        for h in halls:
            hf = db.query(HallFeature).filter(HallFeature.hall_id == h.id)
            if feature_id:
                hf = hf.filter(HallFeature.feature_id == feature_id)
            if option_id:
                hf = hf.filter(HallFeature.option_id == option_id)
            if hf.first():
                keep.append(h)
        halls = keep

    return [
        {"id": h.id, "name": h.name, "capacity": h.capacity,
         "features": _hall_feature_summary(db, h.id)}
        for h in halls
    ]


@router.get("/halls/{hall_id}/availability")
def availability(hall_id: int, on: date, db: Session = Depends(get_db)):
    """Confirmed bookings for a hall on a date, so the client can paint the grid."""
    hall = db.get(Hall, hall_id)
    if not hall or not hall.active:
        raise HTTPException(404, "Hall not found.")
    rows = (
        db.query(Booking)
        .filter(Booking.hall_id == hall_id, Booking.booking_date == on,
                Booking.status == "confirmed")
        .order_by(Booking.start_time)
        .all()
    )
    return {
        "hall": {"id": hall.id, "name": hall.name, "capacity": hall.capacity,
                 "features": _hall_feature_summary(db, hall.id)},
        "date": on.isoformat(),
        "bookings": [
            {"start": b.start_time, "end": b.end_time,
             "booked_by": b.booked_by, "dept": b.dept, "purpose": b.purpose,
             "support_staff_requested": b.support_staff_requested,
             "scientist_designation": b.scientist_designation,
             "project_id": b.project_id,
             "attendees_count": b.attendees_count,
             "features_requested": b.features_requested}
            for b in rows
        ],
    }


@router.post("/bookings")
def book(payload: BookingIn, request: Request, db: Session = Depends(get_db)):
    try:
        b = booking_svc.create_booking(db, payload, _client_ip(request))
    except booking_svc.BookingError as e:
        detail = {"message": e.message}
        if e.conflict:
            detail["conflict"] = {
                "start": e.conflict.start_time, "end": e.conflict.end_time,
                "booked_by": e.conflict.booked_by, "purpose": e.conflict.purpose,
            }
        raise HTTPException(409, detail)
    return {"id": b.id, "cancel_code": b.cancel_code,
            "start": b.start_time, "end": b.end_time,
            "booked_by": b.booked_by, "dept": b.dept,
            "support_staff_requested": b.support_staff_requested,
            "scientist_designation": b.scientist_designation,
            "project_id": b.project_id,
            "attendees_count": b.attendees_count,
            "features_requested": b.features_requested}


@router.post("/bookings/{booking_id}/cancel")
def cancel(booking_id: int, payload: CancelIn, request: Request,
           db: Session = Depends(get_db)):
    try:
        booking_svc.cancel_booking(db, booking_id, payload.cancel_code, _client_ip(request))
    except booking_svc.BookingError as e:
        raise HTTPException(400, e.message)
    return {"status": "cancelled"}

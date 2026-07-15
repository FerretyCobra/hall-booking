"""Public booking API. No login: bookers just supply a name/dept."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from ..config import DAY_START, DAY_END, SLOT_MINUTES
from ..database import get_db
from ..models import Hall, HallFeature, Booking, FeatureCatalog, FeatureOption, DropdownConfig
from ..schemas import BookingIn, CancelIn, BookingUpdateIn
from ..services import bookings as booking_svc
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["public"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
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
def ui_config(db: Session = Depends(get_db)):
    configs = db.query(DropdownConfig).filter(DropdownConfig.active == True).all()
    departments = [c.value for c in configs if c.category == "department"]
    designations = [c.value for c in configs if c.category == "designation"]
    stationery = [c.value for c in configs if c.category == "stationery"]
    return {
        "day_start": DAY_START,
        "day_end": DAY_END,
        "slot_minutes": SLOT_MINUTES,
        "departments": departments,
        "designations": designations,
        "stationery": stationery
    }


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
        {"id": h.id, "name": h.name, "capacity": h.capacity, "image": h.image,
         "requires_approval": h.requires_approval,
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
        "hall": {"id": hall.id, "name": hall.name, "capacity": hall.capacity, "image": hall.image,
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
            "housekeeping_requested": b.housekeeping_requested,
            "scientist_designation": b.scientist_designation,
            "project_id": b.project_id,
            "attendees_count": b.attendees_count,
            "features_requested": b.features_requested,
            "status": b.status,
            "coordinator_name": b.coordinator_name,
            "coordinator_phone": b.coordinator_phone,
            "virtual_meeting_requested": b.virtual_meeting_requested,
            "meeting_link": b.meeting_link,
            "stationery_requested": b.stationery_requested,
            "food_requested": b.food_requested}


@router.post("/bookings/by-code/cancel")
def cancel(payload: CancelIn, request: Request,
           db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.cancel_code == payload.cancel_code.strip().upper()).first()
    if not booking or booking.status not in ("confirmed", "pending_approval"):
        raise HTTPException(404, "Booking not found or already cancelled.")
    try:
        booking_svc.cancel_booking(db, booking.id, payload.cancel_code, _client_ip(request))
    except booking_svc.BookingError as e:
        raise HTTPException(400, e.message)
    return {"status": "cancelled"}


@router.get("/bookings/by-code")
def get_booking(cancel_code: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.cancel_code == cancel_code.strip().upper()).first()
    if not booking:
        raise HTTPException(404, "Booking not found.")
    return {
        "id": booking.id,
        "hall_id": booking.hall_id,
        "booking_date": booking.booking_date.isoformat(),
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "booked_by": booking.booked_by,
        "dept": booking.dept,
        "purpose": booking.purpose,
        "support_staff_requested": booking.support_staff_requested,
        "housekeeping_requested": booking.housekeeping_requested,
        "scientist_designation": booking.scientist_designation,
        "project_id": booking.project_id,
        "attendees_count": booking.attendees_count,
        "features_requested": booking.features_requested,
        "status": booking.status,
        "coordinator_name": booking.coordinator_name,
        "coordinator_phone": booking.coordinator_phone,
        "virtual_meeting_requested": booking.virtual_meeting_requested,
        "meeting_link": booking.meeting_link,
        "stationery_requested": booking.stationery_requested,
        "food_requested": booking.food_requested
    }


@router.post("/bookings/by-code/update")
def update(payload: BookingUpdateIn, request: Request,
           db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.cancel_code == payload.cancel_code.strip().upper()).first()
    if not booking:
        raise HTTPException(404, "Booking not found.")
    try:
        b = booking_svc.update_booking(db, booking.id, payload.cancel_code, payload, _client_ip(request))
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
            "housekeeping_requested": b.housekeeping_requested,
            "scientist_designation": b.scientist_designation,
            "project_id": b.project_id,
            "attendees_count": b.attendees_count,
            "features_requested": b.features_requested,
            "status": b.status,
            "coordinator_name": b.coordinator_name,
            "coordinator_phone": b.coordinator_phone,
            "virtual_meeting_requested": b.virtual_meeting_requested,
            "meeting_link": b.meeting_link,
            "stationery_requested": b.stationery_requested,
            "food_requested": b.food_requested}


from fastapi.responses import HTMLResponse
from ..services.meetings import get_active_meeting_provider
from ..services.notifications import send_booking_confirmation, send_booking_rejection

@router.get("/bookings/approve-by-token", response_class=HTMLResponse)
def approve_by_token_page(token: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.approval_token == token).first()
    if not booking:
        return HTMLResponse("<h2>Error: Invalid or expired approval token.</h2>", status_code=404)
    if booking.status != "pending_approval":
        return HTMLResponse(f"<h2>Notice: Booking is already in '{booking.status}' status.</h2>")
    hall = db.get(Hall, booking.hall_id)
    return HTMLResponse(f"""
    <div style="font-family: sans-serif; text-align: center; margin-top: 100px; max-width: 500px; margin-left: auto; margin-right: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); background: #ffffff;">
        <h2 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 20px;">Confirm Booking Approval</h2>
        <p style="color: #475569; font-size: 15px; line-height: 1.5; margin-bottom: 24px;">Are you sure you want to approve the booking for <strong>{hall.name}</strong> on {booking.booking_date.isoformat()} ({booking.start_time} - {booking.end_time})?</p>
        <form method="POST" action="/api/bookings/approve-by-token?token={token}">
            <button type="submit" style="background-color: #22c55e; color: white; padding: 10px 24px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px;">Yes, Approve Booking</button>
            <a href="/" style="display: inline-block; margin-left: 12px; color: #64748b; text-decoration: none; padding: 10px 20px; font-size: 14px; font-weight: 500;">Cancel</a>
        </form>
    </div>
    """)

@router.post("/bookings/approve-by-token", response_class=HTMLResponse)
def approve_by_token(token: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.approval_token == token).first()
    if not booking:
        return HTMLResponse("<h2>Error: Invalid or expired approval token.</h2>", status_code=404)
    if booking.status != "pending_approval":
        return HTMLResponse(f"<h2>Notice: Booking is already in '{booking.status}' status.</h2>")

    hall = db.get(Hall, booking.hall_id)
    booking.status = "confirmed"
    
    # Generate meeting link if requested
    if booking.virtual_meeting_requested and not booking.meeting_link:
        try:
            provider = get_active_meeting_provider()
            booking.meeting_link = provider.create_meeting(booking.id, booking.purpose or "Meeting")
        except Exception as e:
            logger.error(f"Failed to generate virtual meeting link for confirmed booking {booking.id}: {e}")
            booking.meeting_link = "Pending (Provider Error)"

    db.commit()
    
    try:
        send_booking_confirmation(db, booking, hall)
    except Exception as e:
        print(f"Error sending booking confirmation email: {e}")

    return HTMLResponse("""
    <div style="font-family: sans-serif; text-align: center; margin-top: 100px;">
        <h2 style="color: #22c55e;">✔ Booking Approved Successfully</h2>
        <p>The reservation has been confirmed and a confirmation email has been sent to the coordinator.</p>
        <p><a href="/" style="color: #0284c7; text-decoration: none; font-weight: bold;">Return to Portal</a></p>
    </div>
    """)

@router.get("/bookings/reject-by-token", response_class=HTMLResponse)
def reject_by_token_page(token: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.approval_token == token).first()
    if not booking:
        return HTMLResponse("<h2>Error: Invalid or expired approval token.</h2>", status_code=404)
    if booking.status != "pending_approval":
        return HTMLResponse(f"<h2>Notice: Booking is already in '{booking.status}' status.</h2>")
    hall = db.get(Hall, booking.hall_id)
    return HTMLResponse(f"""
    <div style="font-family: sans-serif; text-align: center; margin-top: 100px; max-width: 500px; margin-left: auto; margin-right: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); background: #ffffff;">
        <h2 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 20px;">Confirm Booking Rejection</h2>
        <p style="color: #475569; font-size: 15px; line-height: 1.5; margin-bottom: 24px;">Are you sure you want to decline the booking for <strong>{hall.name}</strong> on {booking.booking_date.isoformat()} ({booking.start_time} - {booking.end_time})?</p>
        <form method="POST" action="/api/bookings/reject-by-token?token={token}">
            <button type="submit" style="background-color: #dc2626; color: white; padding: 10px 24px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px;">Yes, Decline Booking</button>
            <a href="/" style="display: inline-block; margin-left: 12px; color: #64748b; text-decoration: none; padding: 10px 20px; font-size: 14px; font-weight: 500;">Cancel</a>
        </form>
    </div>
    """)

@router.post("/bookings/reject-by-token", response_class=HTMLResponse)
def reject_by_token(token: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.approval_token == token).first()
    if not booking:
        return HTMLResponse("<h2>Error: Invalid or expired approval token.</h2>", status_code=404)
    if booking.status != "pending_approval":
        return HTMLResponse(f"<h2>Notice: Booking is already in '{booking.status}' status.</h2>")

    hall = db.get(Hall, booking.hall_id)
    booking.status = "cancelled"
    db.commit()

    try:
        send_booking_rejection(db, booking, hall)
    except Exception as e:
        print(f"Error sending booking rejection email: {e}")

    return HTMLResponse("""
    <div style="font-family: sans-serif; text-align: center; margin-top: 100px;">
        <h2 style="color: #dc2626;">✖ Booking Request Declined</h2>
        <p>The reservation request has been rejected and the coordinator has been notified.</p>
        <p><a href="/" style="color: #0284c7; text-decoration: none; font-weight: bold;">Return to Portal</a></p>
    </div>
    """)

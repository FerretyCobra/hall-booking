"""Booking logic. The create path is the one correctness-sensitive spot in the
whole app, so it lives here on its own rather than inline in a router."""
import secrets
import string

from sqlalchemy.orm import Session
import logging

from ..database import transaction
from ..models import Booking, Hall
from . import audit
from .meetings import get_active_meeting_provider

logger = logging.getLogger(__name__)

_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no ambiguous chars


class BookingError(Exception):
    """Raised for user-facing booking failures (validation, clash)."""
    def __init__(self, message, conflict=None):
        super().__init__(message)
        self.message = message
        self.conflict = conflict  # the Booking that blocked this one, if any


def _valid_time(t: str) -> bool:
    if not isinstance(t, str) or len(t) != 5 or t[2] != ":":
        return False
    hh, mm = t[:2], t[3:]
    return hh.isdigit() and mm.isdigit() and 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59


def _new_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))


import secrets

def find_conflict(db: Session, hall_id: int, booking_date, start: str, end: str, exclude_id: int | None = None):
    """Return a confirmed booking that overlaps [start, end) on this hall/date,
    or None. Overlap test: existing.start < end AND existing.end > start."""
    q = db.query(Booking).filter(
        Booking.hall_id == hall_id,
        Booking.booking_date == booking_date,
        Booking.status == "confirmed",
        Booking.start_time < end,
        Booking.end_time > start,
    )
    if exclude_id is not None:
        q = q.filter(Booking.id != exclude_id)
    return q.first()


def create_booking(db: Session, data, ip: str | None) -> Booking:
    """Validate, re-check availability, and insert as a single BEGIN IMMEDIATE
    transaction so two concurrent requests can't both win the same slot."""
    if not _valid_time(data.start_time) or not _valid_time(data.end_time):
        raise BookingError("Times must be in HH:MM 24-hour format.")
    if data.end_time <= data.start_time:
        raise BookingError("End time must be after start time.")
    if not data.booked_by.strip():
        raise BookingError("Please enter who is booking.")

    import datetime
    if data.booking_date < datetime.date.today():
        raise BookingError("Bookings cannot be made for past dates.")

    # One transaction. The engine emits BEGIN IMMEDIATE, so the write lock is
    # held across this check-then-insert.
    with transaction(db):
        hall = db.get(Hall, data.hall_id)
        if not hall or not hall.active:
            raise BookingError("That hall is not available.")

        if data.attendees_count is not None and data.attendees_count > hall.capacity:
            raise BookingError(
                f"Attendees count ({data.attendees_count}) exceeds the maximum capacity of {hall.name} ({hall.capacity})."
            )

        clash = find_conflict(db, data.hall_id, data.booking_date,
                              data.start_time, data.end_time)
        if clash:
            raise BookingError(
                f"{clash.start_time}\u2013{clash.end_time} is already taken "
                f"by {clash.booked_by}.",
                conflict=clash,
            )

        status = "pending_approval" if hall.requires_approval else "confirmed"
        token = secrets.token_urlsafe(16) if status == "pending_approval" else None

        booking = Booking(
            hall_id=data.hall_id,
            booking_date=data.booking_date,
            start_time=data.start_time,
            end_time=data.end_time,
            booked_by=data.booked_by.strip(),
            dept=data.dept,
            purpose=data.purpose,
            status=status,
            cancel_code=_new_code(),
            created_ip=ip,
            support_staff_requested=data.support_staff_requested,
            housekeeping_requested=data.housekeeping_requested,
            scientist_designation=data.scientist_designation,
            project_id=data.project_id,
            attendees_count=data.attendees_count,
            features_requested=data.features_requested,
            coordinator_name=data.coordinator_name,
            coordinator_phone=data.coordinator_phone,
            coordinator_email=data.coordinator_email,
            approval_token=token,
            virtual_meeting_requested=data.virtual_meeting_requested,
            stationery_requested=data.stationery_requested,
            food_requested=data.food_requested,
        )
        db.add(booking)
        db.flush()

        # If confirmed and virtual meeting requested, generate link
        if booking.status == "confirmed" and booking.virtual_meeting_requested:
            try:
                provider = get_active_meeting_provider()
                booking.meeting_link = provider.create_meeting(booking.id, booking.purpose or "Meeting")
            except Exception as e:
                logger.error(f"Failed to generate virtual meeting link for booking {booking.id}: {e}")
                booking.meeting_link = "Pending (Provider Error)"

        audit.log(db, "booking.create", entity="booking", entity_id=booking.id,
                  actor=booking.booked_by, actor_ip=ip,
                  detail=f"{hall.name} {data.booking_date} {data.start_time}-{data.end_time} (status: {status})")

    # Send notifications outside of the transaction block so the database state is committed
    if booking.status == "confirmed":
        from .notifications import send_booking_confirmation
        try:
            send_booking_confirmation(db, booking, hall)
        except Exception as e:
            print(f"Error sending booking confirmation: {e}")
    elif booking.status == "pending_approval":
        from .notifications import send_director_approval_request
        try:
            send_director_approval_request(db, booking, hall)
        except Exception as e:
            print(f"Error sending director approval request: {e}")

    return booking


def cancel_booking(db: Session, booking_id: int, code: str, ip: str | None) -> Booking:
    with transaction(db):
        booking = db.get(Booking, booking_id)
        if not booking or booking.status not in ("confirmed", "pending_approval"):
            raise BookingError("Booking not found or already cancelled.")
        if booking.cancel_code.upper() != (code or "").strip().upper():
            raise BookingError("That cancel code doesn't match.")
        booking.status = "cancelled"
        audit.log(db, "booking.cancel", entity="booking", entity_id=booking.id,
                  actor=booking.booked_by, actor_ip=ip)
    return booking


def update_booking(db: Session, booking_id: int, cancel_code: str, data, ip: str | None) -> Booking:
    if not _valid_time(data.start_time) or not _valid_time(data.end_time):
        raise BookingError("Times must be in HH:MM 24-hour format.")
    if data.end_time <= data.start_time:
        raise BookingError("End time must be after start time.")
    if not data.booked_by.strip():
        raise BookingError("Please enter who is booking.")

    import datetime
    if data.booking_date < datetime.date.today():
        raise BookingError("Bookings cannot be made for past dates.")

    with transaction(db):
        booking = db.get(Booking, booking_id)
        if not booking or booking.status not in ("confirmed", "pending_approval"):
            raise BookingError("Booking not found or already cancelled.")
        if booking.cancel_code.upper() != (cancel_code or "").strip().upper():
            raise BookingError("That cancel code doesn't match.")

        hall = db.get(Hall, data.hall_id)
        if not hall or not hall.active:
            raise BookingError("That hall is not available.")

        if data.attendees_count is not None and data.attendees_count > hall.capacity:
            raise BookingError(
                f"Attendees count ({data.attendees_count}) exceeds the maximum capacity of {hall.name} ({hall.capacity})."
            )

        clash = find_conflict(db, data.hall_id, data.booking_date,
                              data.start_time, data.end_time, exclude_id=booking_id)
        if clash:
            raise BookingError(
                f"{clash.start_time}\u2013{clash.end_time} is already taken "
                f"by {clash.booked_by}.",
                conflict=clash,
            )

        booking.hall_id = data.hall_id
        booking.booking_date = data.booking_date
        booking.start_time = data.start_time
        booking.end_time = data.end_time
        booking.booked_by = data.booked_by.strip()
        booking.dept = data.dept
        booking.purpose = data.purpose
        booking.support_staff_requested = data.support_staff_requested
        booking.housekeeping_requested = data.housekeeping_requested
        booking.scientist_designation = data.scientist_designation
        booking.project_id = data.project_id
        booking.attendees_count = data.attendees_count
        booking.features_requested = data.features_requested
        booking.coordinator_name = data.coordinator_name
        booking.coordinator_phone = data.coordinator_phone
        booking.virtual_meeting_requested = data.virtual_meeting_requested
        booking.stationery_requested = data.stationery_requested
        booking.food_requested = data.food_requested

        # Update meeting link if status changed or requested now
        if booking.status == "confirmed" and booking.virtual_meeting_requested and not booking.meeting_link:
            try:
                provider = get_active_meeting_provider()
                booking.meeting_link = provider.create_meeting(booking.id, booking.purpose or "Meeting")
            except Exception as e:
                logger.error(f"Failed to generate virtual meeting link for booking {booking.id}: {e}")
                booking.meeting_link = "Pending (Provider Error)"
        elif not booking.virtual_meeting_requested:
            booking.meeting_link = None

        db.flush()
        audit.log(db, "booking.update", entity="booking", entity_id=booking.id,
                  actor=booking.booked_by, actor_ip=ip,
                  detail=f"{hall.name} {data.booking_date} {data.start_time}-{data.end_time}")
    return booking

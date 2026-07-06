"""Booking logic. The create path is the one correctness-sensitive spot in the
whole app, so it lives here on its own rather than inline in a router."""
import secrets
import string

from sqlalchemy.orm import Session

from ..database import transaction
from ..models import Booking, Hall
from . import audit

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


def find_conflict(db: Session, hall_id: int, booking_date, start: str, end: str):
    """Return a confirmed booking that overlaps [start, end) on this hall/date,
    or None. Overlap test: existing.start < end AND existing.end > start."""
    return (
        db.query(Booking)
        .filter(
            Booking.hall_id == hall_id,
            Booking.booking_date == booking_date,
            Booking.status == "confirmed",
            Booking.start_time < end,
            Booking.end_time > start,
        )
        .first()
    )


def create_booking(db: Session, data, ip: str | None) -> Booking:
    """Validate, re-check availability, and insert as a single BEGIN IMMEDIATE
    transaction so two concurrent requests can't both win the same slot."""
    if not _valid_time(data.start_time) or not _valid_time(data.end_time):
        raise BookingError("Times must be in HH:MM 24-hour format.")
    if data.end_time <= data.start_time:
        raise BookingError("End time must be after start time.")
    if not data.booked_by.strip():
        raise BookingError("Please enter who is booking.")

    # One transaction. The engine emits BEGIN IMMEDIATE, so the write lock is
    # held across this check-then-insert.
    with transaction(db):
        hall = db.get(Hall, data.hall_id)
        if not hall or not hall.active:
            raise BookingError("That hall is not available.")

        clash = find_conflict(db, data.hall_id, data.booking_date,
                              data.start_time, data.end_time)
        if clash:
            raise BookingError(
                f"{clash.start_time}\u2013{clash.end_time} is already taken "
                f"by {clash.booked_by}.",
                conflict=clash,
            )

        booking = Booking(
            hall_id=data.hall_id,
            booking_date=data.booking_date,
            start_time=data.start_time,
            end_time=data.end_time,
            booked_by=data.booked_by.strip(),
            dept=data.dept,
            purpose=data.purpose,
            status="confirmed",
            cancel_code=_new_code(),
            created_ip=ip,
        )
        db.add(booking)
        db.flush()
        audit.log(db, "booking.create", entity="booking", entity_id=booking.id,
                  actor=booking.booked_by, actor_ip=ip,
                  detail=f"{hall.name} {data.booking_date} {data.start_time}-{data.end_time}")
    return booking


def cancel_booking(db: Session, booking_id: int, code: str, ip: str | None) -> Booking:
    with transaction(db):
        booking = db.get(Booking, booking_id)
        if not booking or booking.status != "confirmed":
            raise BookingError("Booking not found or already cancelled.")
        if booking.cancel_code.upper() != (code or "").strip().upper():
            raise BookingError("That cancel code doesn't match.")
        booking.status = "cancelled"
        audit.log(db, "booking.cancel", entity="booking", entity_id=booking.id,
                  actor=booking.booked_by, actor_ip=ip)
    return booking

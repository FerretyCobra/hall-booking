"""ORM models.

Times are stored as zero-padded "HH:MM" strings. For a single-day, single-site
tool this keeps overlap logic trivial: lexical string comparison of "HH:MM" is
correct, so the overlap test is just `start < other_end AND end > other_start`.
"""
from datetime import datetime, date

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)


class Hall(Base):
    __tablename__ = "halls"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False, default=0)
    image = Column(String, nullable=True)  # custom picture filename/URL
    active = Column(Boolean, nullable=False, default=True)  # soft-delete via active=False
    created_at = Column(DateTime, default=datetime.utcnow)

    features = relationship("HallFeature", back_populates="hall", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="hall")


class FeatureCatalog(Base):
    """A feature *type* the IT team defines. e.g. name='Microphone',
    value_type='multi_select'. Adding a new kind of feature is a data op."""
    __tablename__ = "feature_catalog"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    # bool | number | text | single_select | multi_select
    value_type = Column(String, nullable=False, default="bool")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    options = relationship("FeatureOption", back_populates="feature", cascade="all, delete-orphan")


class FeatureOption(Base):
    """The managed list of allowed values for a select-type feature.
    e.g. under 'Microphone': 'Handheld wireless', 'Lavalier', 'Gooseneck'.
    IT edits this table to add/rename/retire options."""
    __tablename__ = "feature_options"
    id = Column(Integer, primary_key=True)
    feature_id = Column(Integer, ForeignKey("feature_catalog.id"), nullable=False)
    label = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)  # soft-delete
    sort_order = Column(Integer, nullable=False, default=0)

    feature = relationship("FeatureCatalog", back_populates="options")


class HallFeature(Base):
    """What a specific hall has. One row per selected option, so a hall can
    carry several values for the same feature (2 handheld + 1 lavalier)."""
    __tablename__ = "hall_features"
    id = Column(Integer, primary_key=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("feature_catalog.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("feature_options.id"), nullable=True)
    value = Column(String, nullable=True)      # for bool/number/text features
    quantity = Column(Integer, nullable=True)  # e.g. 2 handheld mics

    hall = relationship("Hall", back_populates="features")
    feature = relationship("FeatureCatalog")
    option = relationship("FeatureOption")


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    booking_date = Column(Date, nullable=False)
    start_time = Column(String, nullable=False)  # "HH:MM"
    end_time = Column(String, nullable=False)    # "HH:MM"
    booked_by = Column(String, nullable=False)
    dept = Column(String, nullable=True)
    purpose = Column(String, nullable=True)
    status = Column(String, nullable=False, default="confirmed")  # confirmed | cancelled
    cancel_code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_ip = Column(String, nullable=True)  # accountability, since bookers don't log in

    # ICMR NITVAR fields
    support_staff_requested = Column(Boolean, default=False, nullable=False)
    scientist_designation = Column(String, nullable=True)
    project_id = Column(String, nullable=True)
    attendees_count = Column(Integer, nullable=True)
    features_requested = Column(Text, nullable=True)

    hall = relationship("Hall", back_populates="bookings")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    action = Column(String, nullable=False)     # booking.create, booking.cancel, hall.rename, ...
    entity = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    actor = Column(String, nullable=True)       # booker name or admin username
    actor_ip = Column(String, nullable=True)
    detail = Column(Text, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)

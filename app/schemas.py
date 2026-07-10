"""Pydantic schemas (API request/response shapes)."""
from datetime import date
from typing import Optional, List

from pydantic import BaseModel


# ---- auth ----
class LoginIn(BaseModel):
    username: str
    password: str


class CredentialsUpdateIn(BaseModel):
    new_username: str
    new_password: str


# ---- halls ----
class HallIn(BaseModel):
    name: str
    capacity: int = 0
    image: Optional[str] = None
    requires_approval: bool = False


class HallPatch(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    image: Optional[str] = None
    requires_approval: Optional[bool] = None
    active: Optional[bool] = None


class HallOut(BaseModel):
    id: int
    name: str
    capacity: int
    image: Optional[str] = None
    requires_approval: bool
    active: bool

    class Config:
        from_attributes = True


# ---- features ----
class FeatureIn(BaseModel):
    name: str
    value_type: str = "bool"  # bool | number | text | single_select | multi_select


class FeaturePatch(BaseModel):
    name: Optional[str] = None
    value_type: Optional[str] = None
    active: Optional[bool] = None


class OptionIn(BaseModel):
    label: str
    sort_order: int = 0


class OptionPatch(BaseModel):
    label: Optional[str] = None
    active: Optional[bool] = None
    sort_order: Optional[int] = None


class HallFeatureIn(BaseModel):
    """Assign a feature (and optional option/quantity) to a hall."""
    feature_id: int
    option_id: Optional[int] = None
    value: Optional[str] = None
    quantity: Optional[int] = None


# ---- bookings ----
class BookingIn(BaseModel):
    hall_id: int
    booking_date: date
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    booked_by: str
    dept: Optional[str] = None
    purpose: Optional[str] = None
    support_staff_requested: bool = False
    scientist_designation: Optional[str] = None
    project_id: Optional[str] = None
    attendees_count: Optional[int] = None
    features_requested: Optional[str] = None
    coordinator_name: Optional[str] = None
    coordinator_phone: Optional[str] = None
    coordinator_email: Optional[str] = None
    virtual_meeting_requested: bool = False
    stationery_requested: Optional[str] = None
    food_requested: Optional[str] = None
    housekeeping_requested: bool = False


class BookingUpdateIn(BaseModel):
    cancel_code: str
    booking_date: date
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    booked_by: str
    dept: Optional[str] = None
    purpose: Optional[str] = None
    support_staff_requested: bool = False
    scientist_designation: Optional[str] = None
    project_id: Optional[str] = None
    attendees_count: Optional[int] = None
    features_requested: Optional[str] = None
    coordinator_name: Optional[str] = None
    coordinator_phone: Optional[str] = None
    coordinator_email: Optional[str] = None
    virtual_meeting_requested: bool = False
    stationery_requested: Optional[str] = None
    food_requested: Optional[str] = None
    housekeeping_requested: bool = False


class CancelIn(BaseModel):
    cancel_code: str


class BookingOut(BaseModel):
    id: int
    hall_id: int
    booking_date: date
    start_time: str
    end_time: str
    booked_by: str
    dept: Optional[str] = None
    purpose: Optional[str] = None
    status: str
    support_staff_requested: bool
    housekeeping_requested: bool
    scientist_designation: Optional[str] = None
    project_id: Optional[str] = None
    attendees_count: Optional[int] = None
    features_requested: Optional[str] = None
    coordinator_name: Optional[str] = None
    coordinator_phone: Optional[str] = None
    coordinator_email: Optional[str] = None
    virtual_meeting_requested: bool
    meeting_link: Optional[str] = None
    stationery_requested: Optional[str] = None
    food_requested: Optional[str] = None

    class Config:
        from_attributes = True


# ---- dropdown config ----
class DropdownConfigIn(BaseModel):
    category: str
    value: str


class DropdownConfigOut(BaseModel):
    id: int
    category: str
    value: str
    active: bool

    class Config:
        from_attributes = True

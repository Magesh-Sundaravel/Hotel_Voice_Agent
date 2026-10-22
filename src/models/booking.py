from datetime import UTC, date, datetime
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Reservation(BaseModel):
    id: str
    reference_code: str
    restaurant_id: str
    customer_name: str
    customer_phone: str
    party_size: int
    booking_date: date
    booking_time: str = Field(description="HH:MM format, e.g. '20:00'")
    duration_minutes: int = 90
    table_id: str
    dietary_notes: str | None = None
    special_requests: str | None = None
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AvailabilityCheckRequest(BaseModel):
    booking_date: date
    booking_time: str = Field(description="HH:MM format, e.g. '20:00'")
    party_size: int = Field(ge=1, le=20)


class AvailabilityResponse(BaseModel):
    is_available: bool
    requested_date: date
    requested_time: str
    party_size: int
    matched_table_id: str | None = None
    reason: str | None = None
    alternatives: list[str] = Field(
        default_factory=list, description="Alternative available HH:MM times"
    )


class CreateReservationRequest(BaseModel):
    customer_name: str
    customer_phone: str
    party_size: int = Field(ge=1, le=20)
    booking_date: date
    booking_time: str = Field(description="HH:MM format, e.g. '20:00'")
    dietary_notes: str | None = None
    special_requests: str | None = None


class ModifyReservationRequest(BaseModel):
    reference_code: str
    customer_phone: str
    customer_name: str | None = None
    new_date: date | None = None
    new_time: str | None = None
    new_party_size: int | None = None
    new_dietary_notes: str | None = None


class CancelReservationRequest(BaseModel):
    reference_code: str
    customer_phone: str
    customer_name: str | None = None
    reason: str | None = None


class ServiceResult(BaseModel):
    success: bool
    message: str
    message_it: str
    reservation: Reservation | None = None

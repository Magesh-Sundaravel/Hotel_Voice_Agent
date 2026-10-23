from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class RoomCategory(StrEnum):
    SUPERIOR = "superior"
    DELUXE = "deluxe"
    JUNIOR_SUITE = "junior_suite"
    PANORAMIC_SUITE = "panoramic_suite"


ROOM_CATEGORY_DETAILS = {
    RoomCategory.SUPERIOR: {
        "name_it": "Camera Superior",
        "price_per_night": 250.0,
        "max_guests": 2,
        "description_it": "Camera elegante con letto King-size, bagno in marmo italiano e arredi classici raffinati.",
    },
    RoomCategory.DELUXE: {
        "name_it": "Camera Deluxe con Vista Città",
        "price_per_night": 350.0,
        "max_guests": 2,
        "description_it": "Ampia camera con vista scenografica su Piazza Barberini, salottino e finiture di lusso.",
    },
    RoomCategory.JUNIOR_SUITE: {
        "name_it": "Junior Suite con Balcone",
        "price_per_night": 480.0,
        "max_guests": 3,
        "description_it": "Junior Suite con balcone privato affacciato sul centro storico, zona living e doccia cromoterapica.",
    },
    RoomCategory.PANORAMIC_SUITE: {
        "name_it": "Suite Panoramica Barberini",
        "price_per_night": 750.0,
        "max_guests": 4,
        "description_it": "Prestigiosa suite all'ultimo piano con terrazza privata panoramica a 360° su Roma, idromassaggio e maggiordomo.",
        "features_it": "terrazza 360°, idromassaggio",
    },
}


class RoomBookingStatus(StrEnum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    EARLY_DEPARTURE = "early_departure"
    CANCELLED = "cancelled"


class HotelRoom(BaseModel):
    room_number: str
    category: RoomCategory
    name: str
    price_per_night: float
    max_guests: int
    floor: int
    features: list[str] = Field(default_factory=list)
    is_clean: bool = True
    is_active: bool = True


class RoomBooking(BaseModel):
    id: str
    reference_code: str = Field(description="Es. SINA-1042")
    hotel_id: str = "sina_bernini_bristol"
    guest_name: str
    guest_phone: str
    guest_email: str | None = None
    room_number: str
    room_category: RoomCategory
    check_in_date: date
    check_out_date: date
    nights: int
    guests_count: int = Field(ge=1, le=4)
    price_per_night: float
    total_price: float
    special_requests: str | None = None
    is_early_check_in: bool = False
    is_early_departure: bool = False
    early_departure_reason: str | None = None
    actual_departure_date: date | None = None
    status: RoomBookingStatus = RoomBookingStatus.CONFIRMED
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AvailableCategoryOption(BaseModel):
    category: RoomCategory
    name_it: str
    price_per_night: float
    total_price: float
    max_guests: int
    available_rooms_count: int
    description_it: str


class RoomAvailabilityResponse(BaseModel):
    is_available: bool
    check_in_date: date
    check_out_date: date
    nights: int
    guests_count: int
    options: list[AvailableCategoryOption] = Field(default_factory=list)
    message_it: str


class CreateRoomBookingRequest(BaseModel):
    guest_name: str
    guest_phone: str
    guest_email: str | None = None
    category: RoomCategory
    check_in_date: date
    check_out_date: date
    guests_count: int = Field(default=2, ge=1, le=4)
    special_requests: str | None = None
    is_early_check_in: bool = False


class ModifyRoomBookingRequest(BaseModel):
    reference_code: str
    guest_phone: str
    new_check_in_date: date | None = None
    new_check_out_date: date | None = None
    new_category: RoomCategory | None = None
    new_guests_count: int | None = None
    new_special_requests: str | None = None


class MarkEarlyDepartureRequest(BaseModel):
    reference_code: str
    guest_phone: str
    actual_departure_date: date | None = None
    reason: str | None = None


class RoomBookingServiceResult(BaseModel):
    success: bool
    message_it: str
    booking: RoomBooking | None = None

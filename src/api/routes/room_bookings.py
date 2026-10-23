from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.models.hotel_booking import (
    AvailableCategoryOption,
    CreateRoomBookingRequest,
    HotelRoom,
    MarkEarlyDepartureRequest,
    ModifyRoomBookingRequest,
    RoomAvailabilityResponse,
    RoomBooking,
    RoomBookingServiceResult,
    RoomBookingStatus,
    RoomCategory,
)
from src.repositories import (
    get_guest_crm_repository,
    get_hotel_room_repository,
    get_notification_repository,
)
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService

router = APIRouter(prefix="/api", tags=["Sina Hotel Rooms & Bookings"])


def get_hotel_booking_service(request: Request) -> HotelBookingService:
    if hasattr(getattr(request, "app", None), "state"):
        svc = getattr(request.app.state, "hotel_booking_service", None)
        if svc is not None:
            return svc
    crm_service = GuestCRMService(
        crm_repo=get_guest_crm_repository(),
        notification_repo=get_notification_repository(),
        default_hotel_id="sina_bernini_bristol",
    )
    return HotelBookingService(
        room_repo=get_hotel_room_repository(),
        notification_repo=get_notification_repository(),
        guest_crm_service=crm_service,
        hotel_id="sina_bernini_bristol",
    )


class CheckAvailabilityQuery(BaseModel):
    check_in_date: date
    check_out_date: date
    guests_count: int = Field(default=2, ge=1, le=4)
    category: RoomCategory | None = None


class CancelBookingQuery(BaseModel):
    reference_code: str
    guest_phone: str
    reason: str | None = None


@router.get("/rooms", response_model=list[HotelRoom])
async def list_rooms(
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Retrieve all Sina Bernini Bristol hotel rooms with status and features."""
    return await service.room_repo.get_all_rooms()


@router.get("/room-bookings", response_model=list[RoomBooking])
async def list_bookings(
    status: RoomBookingStatus | None = Query(None, description="Filter by status"),
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Retrieve all hotel room bookings, optionally filtered by status (in-house, early departure, etc.)."""
    all_b = await service.room_repo.get_all_bookings()
    if status:
        return [b for b in all_b if b.status == status]
    return all_b


@router.get("/room-bookings/{reference_code}", response_model=RoomBooking)
async def get_booking_by_ref(
    reference_code: str,
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Get single room booking by reference code (e.g. SINA-4020)."""
    b = await service.room_repo.get_booking_by_ref(reference_code)
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b


@router.post("/room-bookings/check-availability", response_model=RoomAvailabilityResponse)
async def check_availability_endpoint(
    body: CheckAvailabilityQuery,
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Check room availability across date ranges and get room options & prices."""
    return await service.check_availability(
        check_in_date=body.check_in_date,
        check_out_date=body.check_out_date,
        guests_count=body.guests_count,
        category=body.category,
    )


@router.post("/room-bookings", response_model=RoomBookingServiceResult)
async def create_booking_endpoint(
    body: CreateRoomBookingRequest,
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Create a new confirmed hotel room booking."""
    return await service.create_booking(body)


@router.post("/room-bookings/modify", response_model=RoomBookingServiceResult)
async def modify_booking_endpoint(
    body: ModifyRoomBookingRequest,
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Modify dates, category, or guests count of an existing reservation."""
    return await service.modify_booking(body)


@router.post("/room-bookings/cancel", response_model=RoomBookingServiceResult)
async def cancel_booking_endpoint(
    body: CancelBookingQuery,
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Cancel a hotel room reservation."""
    return await service.cancel_booking(
        reference_code=body.reference_code,
        guest_phone=body.guest_phone,
        reason=body.reason,
    )


@router.post("/room-bookings/early-departure", response_model=RoomBookingServiceResult)
async def early_departure_endpoint(
    body: MarkEarlyDepartureRequest,
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Record guest early departure, freeing the room and recalculating nights."""
    return await service.mark_early_departure(body)


@router.get("/hotel-stats")
async def get_hotel_stats(
    service: HotelBookingService = Depends(get_hotel_booking_service),
):
    """Get high-level hotel KPIs (occupancy, arrivals today, in-house, early departures)."""
    today = date.today()
    rooms = await service.room_repo.get_all_rooms()
    bookings = await service.room_repo.get_all_bookings()

    in_house = [
        b
        for b in bookings
        if b.status == RoomBookingStatus.CHECKED_IN
        or (
            b.status == RoomBookingStatus.CONFIRMED
            and b.check_in_date <= today < b.check_out_date
        )
    ]
    arrivals_today = [
        b
        for b in bookings
        if b.check_in_date == today and b.status != RoomBookingStatus.CANCELLED
    ]
    departures_today = [
        b
        for b in bookings
        if b.check_out_date == today and b.status != RoomBookingStatus.CANCELLED
    ]
    early_departures = [
        b for b in bookings if b.status == RoomBookingStatus.EARLY_DEPARTURE
    ]

    total_rooms = len(rooms)
    occupied_count = len(in_house)
    rate = round((occupied_count / total_rooms) * 100, 1) if total_rooms > 0 else 0.0

    return {
        "hotel_name": "Sina Bernini Bristol",
        "city": "Roma",
        "today": str(today),
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_count,
        "occupancy_rate_percentage": rate,
        "in_house_guests_count": occupied_count,
        "arrivals_today_count": len(arrivals_today),
        "departures_today_count": len(departures_today),
        "early_departures_count": len(early_departures),
    }

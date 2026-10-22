from datetime import date

from fastapi import APIRouter, HTTPException, Query

from src.models import (
    AvailabilityResponse,
    BookingStatus,
    CRMNotification,
    Reservation,
)
from src.repositories import (
    get_booking_repository,
    get_notification_repository,
    get_restaurant_repository,
)
from src.services.availability_service import AvailabilityService

router = APIRouter(prefix="/api", tags=["CRM & Reservations"])


@router.get("/reservations", response_model=list[Reservation])
async def list_reservations(
    booking_date: date | None = None,
    restaurant_id: str = "default_trattoria",
    status: BookingStatus | None = None,
):
    target_date = booking_date or date.today()
    repo = get_booking_repository()
    return await repo.get_reservations_for_date(
        restaurant_id=restaurant_id,
        booking_date=target_date,
        status=status,
    )


@router.get("/notifications", response_model=list[CRMNotification])
async def list_crm_notifications(
    restaurant_id: str = "default_trattoria",
    unread_only: bool = False,
    limit: int = 50,
):
    repo = get_notification_repository()
    return await repo.get_notifications(
        restaurant_id=restaurant_id,
        unread_only=unread_only,
        limit=limit,
    )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    repo = get_notification_repository()
    success = await repo.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok", "message": "Marked as read"}


@router.get("/availability", response_model=AvailabilityResponse)
async def check_availability_endpoint(
    booking_date: date,
    booking_time: str,
    party_size: int = Query(..., ge=1, le=20),
    restaurant_id: str = "default_trattoria",
):
    rest_repo = get_restaurant_repository()
    book_repo = get_booking_repository()
    svc = AvailabilityService(rest_repo, book_repo)
    return await svc.check_availability(
        restaurant_id=restaurant_id,
        booking_date=booking_date,
        booking_time_str=booking_time,
        party_size=party_size,
    )

import json
from datetime import date, timedelta

import pytest

from src.repositories.hotel_room_repo import InMemoryHotelRoomRepository
from src.repositories.memory_repo import (
    InMemoryGuestCRMRepository,
    InMemoryNotificationRepository,
)
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService
from src.tools.hotel_room_tools import (
    CheckRoomAvailabilityTool,
    CreateHotelRoomBookingTool,
    ModifyHotelRoomBookingTool,
)


@pytest.fixture
def hotel_booking_service():
    room_repo = InMemoryHotelRoomRepository()
    notif_repo = InMemoryNotificationRepository()
    crm_repo = InMemoryGuestCRMRepository()
    crm_svc = GuestCRMService(crm_repo, notif_repo)
    return HotelBookingService(
        room_repo=room_repo,
        notification_repo=notif_repo,
        guest_crm_service=crm_svc,
        hotel_id="sina_bernini_bristol",
    )


@pytest.mark.asyncio
async def test_check_availability_invalid_date(hotel_booking_service):
    tool = CheckRoomAvailabilityTool(booking_service=hotel_booking_service)
    result_raw = await tool._arun(
        check_in_date="not-a-date",
        check_out_date="2026-10-25",
    )
    result = json.loads(result_raw)
    assert result["is_available"] is False
    assert "Formato data non valido" in result["message_it"]


@pytest.mark.asyncio
async def test_check_availability_invalid_category(hotel_booking_service):
    tool = CheckRoomAvailabilityTool(booking_service=hotel_booking_service)
    d_in = (date.today() + timedelta(days=5)).isoformat()
    d_out = (date.today() + timedelta(days=7)).isoformat()
    result_raw = await tool._arun(
        check_in_date=d_in,
        check_out_date=d_out,
        category="invalid_category",
    )
    result = json.loads(result_raw)
    assert result["is_available"] is False
    assert "non valida" in result["message_it"]


@pytest.mark.asyncio
async def test_create_booking_invalid_date(hotel_booking_service):
    tool = CreateHotelRoomBookingTool(booking_service=hotel_booking_service)
    result_raw = await tool._arun(
        guest_name="Marco Rossi",
        guest_phone="+393331112222",
        category="deluxe",
        check_in_date="invalid-date",
        check_out_date="2026-11-01",
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "Formato data non valido" in result["message_it"]


@pytest.mark.asyncio
async def test_create_booking_invalid_category(hotel_booking_service):
    tool = CreateHotelRoomBookingTool(booking_service=hotel_booking_service)
    d_in = (date.today() + timedelta(days=5)).isoformat()
    d_out = (date.today() + timedelta(days=7)).isoformat()
    result_raw = await tool._arun(
        guest_name="Marco Rossi",
        guest_phone="+393331112222",
        category="penthouse_royal",
        check_in_date=d_in,
        check_out_date=d_out,
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "non valida" in result["message_it"]


@pytest.mark.asyncio
async def test_modify_booking_invalid_date(hotel_booking_service):
    tool = ModifyHotelRoomBookingTool(booking_service=hotel_booking_service)
    result_raw = await tool._arun(
        reference_code="SINA-1000",
        guest_phone="+393331112222",
        new_check_in_date="invalid-date",
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "Formato data non valido" in result["message_it"]


@pytest.mark.asyncio
async def test_modify_booking_invalid_category(hotel_booking_service):
    tool = ModifyHotelRoomBookingTool(booking_service=hotel_booking_service)
    result_raw = await tool._arun(
        reference_code="SINA-1000",
        guest_phone="+393331112222",
        new_category="unknown_suite",
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "non valida" in result["message_it"]

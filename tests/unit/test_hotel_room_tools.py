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
from src.voice.session import CallSession
from src.voice.tools import execute_tool_call


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


@pytest.fixture
def call_session():
    session = CallSession(call_id="test_hotel_call", user_id="test_user", caller_phone="+393331112222")
    session.read_back_confirmed = True
    return session


@pytest.mark.asyncio
async def test_check_availability_invalid_date(hotel_booking_service, call_session):
    result_raw = await execute_tool_call(
        tool_name="check_room_availability",
        raw_args={
            "check_in_date": "not-a-date",
            "check_out_date": "2026-10-25",
        },
        session=call_session,
        hotel_booking_service=hotel_booking_service,
    )
    result = json.loads(result_raw)
    assert result["is_available"] is False
    assert "Formato data non valido" in result["message_it"]


@pytest.mark.asyncio
async def test_check_availability_invalid_category(hotel_booking_service, call_session):
    d_in = (date.today() + timedelta(days=5)).isoformat()
    d_out = (date.today() + timedelta(days=7)).isoformat()
    result_raw = await execute_tool_call(
        tool_name="check_room_availability",
        raw_args={
            "check_in_date": d_in,
            "check_out_date": d_out,
            "category": "invalid_category",
        },
        session=call_session,
        hotel_booking_service=hotel_booking_service,
    )
    result = json.loads(result_raw)
    assert result["is_available"] is False
    assert "non valida" in result["message_it"]


@pytest.mark.asyncio
async def test_create_booking_invalid_date(hotel_booking_service, call_session):
    result_raw = await execute_tool_call(
        tool_name="create_hotel_room_booking",
        raw_args={
            "guest_name": "Marco Rossi",
            "guest_phone": "+393331112222",
            "category": "deluxe",
            "check_in_date": "invalid-date",
            "check_out_date": "2026-11-01",
        },
        session=call_session,
        hotel_booking_service=hotel_booking_service,
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "Formato data non valido" in result["message_it"]


@pytest.mark.asyncio
async def test_create_booking_invalid_category(hotel_booking_service, call_session):
    d_in = (date.today() + timedelta(days=5)).isoformat()
    d_out = (date.today() + timedelta(days=7)).isoformat()
    result_raw = await execute_tool_call(
        tool_name="create_hotel_room_booking",
        raw_args={
            "guest_name": "Marco Rossi",
            "guest_phone": "+393331112222",
            "category": "penthouse_royal",
            "check_in_date": d_in,
            "check_out_date": d_out,
        },
        session=call_session,
        hotel_booking_service=hotel_booking_service,
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "non valida" in result["message_it"]


@pytest.mark.asyncio
async def test_modify_booking_invalid_date(hotel_booking_service, call_session):
    result_raw = await execute_tool_call(
        tool_name="modify_hotel_room_booking",
        raw_args={
            "reference_code": "SINA-1000",
            "guest_phone": "+393331112222",
            "new_check_in_date": "invalid-date",
        },
        session=call_session,
        hotel_booking_service=hotel_booking_service,
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "Formato data non valido" in result["message_it"]


@pytest.mark.asyncio
async def test_modify_booking_invalid_category(hotel_booking_service, call_session):
    result_raw = await execute_tool_call(
        tool_name="modify_hotel_room_booking",
        raw_args={
            "reference_code": "SINA-1000",
            "guest_phone": "+393331112222",
            "new_category": "unknown_suite",
        },
        session=call_session,
        hotel_booking_service=hotel_booking_service,
    )
    result = json.loads(result_raw)
    assert result["success"] is False
    assert "non valida" in result["message_it"]

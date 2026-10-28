import json

import pytest

from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.voice.session import CallSession
from src.voice.tools import execute_tool_call, get_all_tool_schemas


@pytest.mark.asyncio
async def test_email_confirmation_tool_valid():
    email_service = EmailService()
    session = CallSession(call_id="test_call", user_id="test_user", caller_phone="+393331112233")

    raw_res = await execute_tool_call(
        tool_name="send_booking_confirmation_email",
        raw_args={
            "guest_email": "test.ospite@gmail.com",
            "guest_name": "Mario Rossi",
            "reference_code": "SINA-4020",
            "room_category": "Camera Deluxe con Vista Città",
            "check_in_date": "2026-10-25",
            "check_out_date": "2026-10-28",
            "guests_count": 2,
            "total_price": 1050,
            "room_number": "301",
        },
        session=session,
        email_service=email_service,
    )
    res = json.loads(raw_res)
    assert res["success"] is True
    assert "test.ospite@gmail.com" in res["message_it"]


@pytest.mark.asyncio
async def test_email_confirmation_tool_invalid():
    email_service = EmailService()
    session = CallSession(call_id="test_call", user_id="test_user", caller_phone="+393331112233")

    raw_res = await execute_tool_call(
        tool_name="send_booking_confirmation_email",
        raw_args={
            "guest_email": "invalid-email-address",
            "guest_name": "Mario Rossi",
            "reference_code": "SINA-4020",
            "room_category": "Superior",
            "check_in_date": "2026-10-25",
            "check_out_date": "2026-10-28",
        },
        session=session,
        email_service=email_service,
    )
    res = json.loads(raw_res)
    assert res["success"] is False
    assert "non sembra valido" in res["message_it"]


@pytest.mark.asyncio
async def test_sms_confirmation_tool():
    twilio_service = TwilioService()
    session = CallSession(call_id="test_call", user_id="test_user", caller_phone="+393331234567")

    raw_res = await execute_tool_call(
        tool_name="send_booking_confirmation_sms",
        raw_args={
            "guest_phone": "+393331234567",
            "guest_name": "Mario Rossi",
            "reference_code": "SINA-4020",
            "room_category": "Junior Suite",
            "check_in_date": "2026-10-25",
            "check_out_date": "2026-10-28",
        },
        session=session,
        twilio_service=twilio_service,
    )
    res = json.loads(raw_res)
    assert res["success"] is True
    assert "+393331234567" in res["message_it"]


def test_build_communication_tools_schemas():
    schemas = get_all_tool_schemas(include_hotel=True, include_restaurant=False)
    names = {s["function"]["name"] for s in schemas}
    assert "send_booking_confirmation_email" in names
    assert "send_booking_confirmation_sms" in names

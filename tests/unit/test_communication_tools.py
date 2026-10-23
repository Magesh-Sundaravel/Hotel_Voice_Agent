import json

import pytest

from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.tools.communication_tools import (
    SendBookingConfirmationEmailTool,
    SendBookingConfirmationSmsTool,
    build_communication_tools,
)


@pytest.mark.asyncio
async def test_email_confirmation_tool_valid():
    email_service = EmailService()
    tool = SendBookingConfirmationEmailTool(email_service=email_service)

    raw_res = await tool._arun(
        guest_email="test.ospite@gmail.com",
        guest_name="Mario Rossi",
        reference_code="SINA-4020",
        room_category="Camera Deluxe con Vista Città",
        check_in_date="2026-10-25",
        check_out_date="2026-10-28",
        guests_count=2,
        total_price=1050,
        room_number="301",
    )
    res = json.loads(raw_res)
    assert res["success"] is True
    assert "test.ospite@gmail.com" in res["message_it"]


@pytest.mark.asyncio
async def test_email_confirmation_tool_invalid():
    email_service = EmailService()
    tool = SendBookingConfirmationEmailTool(email_service=email_service)

    raw_res = await tool._arun(
        guest_email="invalid-email-address",
        guest_name="Mario Rossi",
        reference_code="SINA-4020",
        room_category="Superior",
        check_in_date="2026-10-25",
        check_out_date="2026-10-28",
    )
    res = json.loads(raw_res)
    assert res["success"] is False
    assert "non sembra valido" in res["message_it"]


@pytest.mark.asyncio
async def test_sms_confirmation_tool():
    twilio_service = TwilioService()
    tool = SendBookingConfirmationSmsTool(twilio_service=twilio_service)

    raw_res = await tool._arun(
        guest_phone="+393331234567",
        guest_name="Mario Rossi",
        reference_code="SINA-4020",
        room_category="Junior Suite",
        check_in_date="2026-10-25",
        check_out_date="2026-10-28",
    )
    res = json.loads(raw_res)
    assert res["success"] is True
    assert "+393331234567" in res["message_it"]


def test_build_communication_tools():
    tools = build_communication_tools()
    assert len(tools) == 2
    names = {t.name for t in tools}
    assert "send_booking_confirmation_email" in names
    assert "send_booking_confirmation_sms" in names

import json

import pytest

from src.voice.session import CallSession
from src.voice.tools import execute_tool_call


@pytest.fixture
def call_session():
    return CallSession(call_id="test_crm_call", user_id="test_user", caller_phone="+39 333 1112233")


@pytest.mark.asyncio
async def test_lookup_caller_tool(guest_crm_service, call_session):
    res_str = await execute_tool_call(
        tool_name="lookup_caller_crm",
        raw_args={"phone_number": "+39 333 1112233"},
        session=call_session,
        guest_crm_service=guest_crm_service,
    )
    data = json.loads(res_str)
    assert data["is_known_guest"] is True
    assert data["last_name"] == "Rossi"
    assert data["room_number"] == "402"
    assert data["stage"] == "in_house"


@pytest.mark.asyncio
async def test_record_preference_tool(guest_crm_service, call_session):
    res_str = await execute_tool_call(
        tool_name="record_guest_preference",
        raw_args={
            "phone_number": "+39 333 1112233",
            "dietary_restriction": "No crostacei",
            "room_preference": "Piano attico",
        },
        session=call_session,
        guest_crm_service=guest_crm_service,
    )
    data = json.loads(res_str)
    assert data["success"] is True
    assert "No crostacei" in data["current_dietary"]


@pytest.mark.asyncio
async def test_record_title_preference_tool(guest_crm_service, call_session):
    res_str = await execute_tool_call(
        tool_name="record_guest_preference",
        raw_args={
            "phone_number": "+39 333 9998877",
            "title": "Signor",
            "special_note": "Preferisce titolo formale",
        },
        session=call_session,
        guest_crm_service=guest_crm_service,
    )
    data = json.loads(res_str)
    assert data["success"] is True

    res_lookup = await execute_tool_call(
        tool_name="lookup_caller_crm",
        raw_args={"phone_number": "+39 333 9998877"},
        session=call_session,
        guest_crm_service=guest_crm_service,
    )
    data_lookup = json.loads(res_lookup)
    assert data_lookup["title"] == "Signor"


@pytest.mark.asyncio
async def test_request_concierge_service_tool(guest_crm_service, call_session):
    res_str = await execute_tool_call(
        tool_name="request_concierge_service",
        raw_args={
            "phone_number": "+39 335 9988776",
            "category": "transport",
            "title": "Transfer NCC da Fiumicino",
            "details": "Arrivo volo ore 15:00 con 1 valigia",
            "scheduled_time": "15:00",
        },
        session=call_session,
        guest_crm_service=guest_crm_service,
    )
    data = json.loads(res_str)
    assert data["success"] is True
    assert "NCC" in data["title"]


@pytest.mark.asyncio
async def test_get_city_recommendations_tool(guest_crm_service, call_session):
    res_str = await execute_tool_call(
        tool_name="get_city_recommendations",
        raw_args={"phone_number": "+39 333 1112233"},
        session=call_session,
        guest_crm_service=guest_crm_service,
    )
    data = json.loads(res_str)
    recs = data["recommendations"]
    assert len(recs) > 0
    assert any("The Flair" in r["title"] for r in recs)


@pytest.mark.asyncio
async def test_submit_guest_feedback_tool(guest_crm_service, call_session):
    res_str = await execute_tool_call(
        tool_name="submit_guest_feedback",
        raw_args={
            "phone_number": "+39 340 5544332",
            "nps_score": 10,
            "comments": "Bellissimo soggiorno al Bernini Bristol!",
        },
        session=call_session,
        guest_crm_service=guest_crm_service,
    )
    data = json.loads(res_str)
    assert data["success"] is True
    assert "request_id" in data or "message_it" in data

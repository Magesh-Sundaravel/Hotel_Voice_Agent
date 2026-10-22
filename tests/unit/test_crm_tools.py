import json
import pytest

from src.models import ConciergeCategory, TravelPersona
from src.tools.crm_tools import (
    GetCityRecommendationsTool,
    LookupCallerCRMTool,
    RecordGuestPreferenceTool,
    RequestConciergeServiceTool,
    SubmitGuestFeedbackTool,
    build_crm_tools,
)


@pytest.fixture
def crm_tools(guest_crm_service):
    return {t.name: t for t in build_crm_tools(guest_crm_service)}


@pytest.mark.asyncio
async def test_lookup_caller_tool(crm_tools):
    tool = crm_tools["lookup_caller_crm"]
    res_str = await tool._arun(phone_number="+39 333 1112233")
    data = json.loads(res_str)
    assert data["is_known_guest"] is True
    assert data["last_name"] == "Rossi"
    assert data["room_number"] == "402"
    assert data["stage"] == "in_house"


@pytest.mark.asyncio
async def test_record_preference_tool(crm_tools):
    tool = crm_tools["record_guest_preference"]
    res_str = await tool._arun(
        phone_number="+39 333 1112233",
        dietary_restriction="No crostacei",
        room_preference="Piano attico",
    )
    data = json.loads(res_str)
    assert data["success"] is True
    assert "No crostacei" in data["current_dietary"]


@pytest.mark.asyncio
async def test_request_concierge_service_tool(crm_tools):
    tool = crm_tools["request_concierge_service"]
    res_str = await tool._arun(
        phone_number="+39 335 9988776",
        category="transport",
        title="Transfer NCC da Fiumicino",
        details="Arrivo volo ore 15:00 con 1 valigia",
        scheduled_time="15:00",
    )
    data = json.loads(res_str)
    assert data["success"] is True
    assert "NCC" in data["title"]


@pytest.mark.asyncio
async def test_get_city_recommendations_tool(crm_tools):
    tool = crm_tools["get_city_recommendations"]
    res_str = await tool._arun(phone_number="+39 333 1112233")
    data = json.loads(res_str)
    recs = data["recommendations"]
    assert len(recs) > 0
    assert any("The Flair" in r["title"] for r in recs)


@pytest.mark.asyncio
async def test_submit_guest_feedback_tool(crm_tools):
    tool = crm_tools["submit_guest_feedback"]
    res_str = await tool._arun(
        phone_number="+39 340 5544332",
        nps_score=10,
        comments="Bellissimo soggiorno al Bernini Bristol!",
    )
    data = json.loads(res_str)
    assert data["success"] is True
    assert "feedback_id" in data

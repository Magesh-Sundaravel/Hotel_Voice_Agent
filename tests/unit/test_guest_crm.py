import pytest

from src.models import (
    ConciergeCategory,
    NotificationType,
    StayStage,
    TravelPersona,
    VIPTier,
)


@pytest.mark.asyncio
async def test_in_house_romantic_guest_lookup(guest_crm_service):
    # Marco Rossi - In House Room 402 with Giulia (10th Anniversary)
    context = await guest_crm_service.lookup_caller_context("+39 333 1112233")
    assert context.is_known_guest is True
    assert context.guest is not None
    assert context.guest.last_name == "Rossi"
    assert context.guest.vip_tier == VIPTier.GOLD
    assert context.guest.persona == TravelPersona.ROMANTIC_COUPLE
    assert context.stage == StayStage.IN_HOUSE
    assert context.stay is not None
    assert context.stay.room_number == "402"
    assert "camera 402" in context.suggested_greeting_it.lower()
    assert "Signor Rossi" in context.suggested_greeting_it


@pytest.mark.asyncio
async def test_pre_stay_business_guest_lookup(guest_crm_service):
    # Andrea Moretti - Pre-Stay VIP Member
    context = await guest_crm_service.lookup_caller_context("+39 335 9988776")
    assert context.is_known_guest is True
    assert context.guest.vip_tier == VIPTier.SINA_PRIVILEGE_VIP
    assert context.stage == StayStage.PRE_STAY
    assert "prossimo soggiorno" in context.suggested_greeting_it.lower()


@pytest.mark.asyncio
async def test_post_stay_guest_lookup(guest_crm_service):
    # Elena Bianchi - Post-Stay Family
    context = await guest_crm_service.lookup_caller_context("+39 340 5544332")
    assert context.is_known_guest is True
    assert context.stage == StayStage.POST_STAY
    assert "Signora Bianchi" in context.suggested_greeting_it


@pytest.mark.asyncio
async def test_unknown_caller_lookup(guest_crm_service):
    context = await guest_crm_service.lookup_caller_context("+39 399 0000000")
    assert context.is_known_guest is False
    assert context.guest is None
    assert context.stay is None
    assert context.stage == StayStage.NON_RESIDENT
    assert "Concierge al Suo servizio" in context.suggested_greeting_it


@pytest.mark.asyncio
async def test_save_guest_preference_triggers_allergy_alert(guest_crm_service, notification_repo):
    phone = "+39 333 1112233"
    updated_guest = await guest_crm_service.save_guest_preference(
        phone=phone,
        dietary_restriction="allergia ai crostacei",
        room_preference="cuscini extra morbidi",
    )
    assert "allergia ai crostacei" in updated_guest.preferences.dietary_restrictions
    assert "cuscini extra morbidi" in updated_guest.preferences.room_preferences

    # Check notification was dispatched
    notifs = await notification_repo.get_notifications(restaurant_id="sina_bernini_bristol")
    allergy_alerts = [n for n in notifs if n.type == NotificationType.ALLERGY_ALERT]
    assert len(allergy_alerts) >= 1
    assert "crostacei" in allergy_alerts[0].message.lower()


@pytest.mark.asyncio
async def test_create_concierge_transport_request(guest_crm_service, notification_repo):
    req = await guest_crm_service.create_concierge_request(
        phone="+39 335 9988776",
        category=ConciergeCategory.TRANSPORT,
        title="Transfer NCC Mercedes da FCO",
        details="Volo AZ1234 in arrivo da Milano Linate alle 14:15. Bagaglio a mano.",
        scheduled_time="14:15",
    )
    assert req.id.startswith("req_")
    assert req.category == ConciergeCategory.TRANSPORT

    notifs = await notification_repo.get_notifications(restaurant_id="sina_bernini_bristol")
    transfer_alerts = [n for n in notifs if n.type == NotificationType.TRANSFER_REQUEST]
    assert len(transfer_alerts) >= 1
    assert "AZ1234" in transfer_alerts[0].message


@pytest.mark.asyncio
async def test_personalized_city_recommendations(guest_crm_service):
    # Marco Rossi is ROMANTIC_COUPLE
    recs = await guest_crm_service.get_personalized_recommendations(
        phone="+39 333 1112233",
        category=None,
    )
    assert len(recs) > 0
    # Top recommendations should be suitable for romantic couple
    assert TravelPersona.ROMANTIC_COUPLE in recs[0].recommended_for


@pytest.mark.asyncio
async def test_guest_feedback_submission(guest_crm_service, notification_repo):
    fb = await guest_crm_service.record_feedback(
        phone="+39 340 5544332",
        nps_score=10,
        comments="Esperienza magnifica con i bambini al Sina Bernini Bristol!",
    )
    assert fb.nps_score == 10
    notifs = await notification_repo.get_notifications(restaurant_id="sina_bernini_bristol")
    fb_alerts = [n for n in notifs if n.type == NotificationType.GUEST_FEEDBACK]
    assert len(fb_alerts) >= 1
    assert "10/10" in fb_alerts[0].title


@pytest.mark.asyncio
async def test_guest_greeting_without_title_uses_first_name(guest_crm_service):
    # Register a guest with no title specified
    phone = "+39 333 7778899"
    await guest_crm_service.save_guest_preference(
        phone=phone,
        special_note="First time inquiry",
    )
    # The default created profile has first_name="Ospite", title=None
    ctx = await guest_crm_service.lookup_caller_context(phone)
    assert ctx.is_known_guest is True
    assert ctx.guest.title is None
    # Greets using first name ("Ospite") without any forced "Signor" or "Signora" prefix
    assert "Buongiorno Ospite!" in ctx.suggested_greeting_it


@pytest.mark.asyncio
async def test_set_and_update_guest_title(guest_crm_service):
    phone = "+39 333 4445566"
    guest = await guest_crm_service.save_guest_preference(
        phone=phone,
        title="Signor",
    )
    assert guest.title == "Signor"

    ctx = await guest_crm_service.lookup_caller_context(phone)
    assert "Buongiorno Signor Registrato!" in ctx.suggested_greeting_it

    # Update title
    updated = await guest_crm_service.save_guest_preference(
        phone=phone,
        title="Signora",
    )
    assert updated.title == "Signora"
    ctx_updated = await guest_crm_service.lookup_caller_context(phone)
    assert "Buongiorno Signora Registrato!" in ctx_updated.suggested_greeting_it

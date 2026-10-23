from datetime import date, timedelta

import pytest

from src.models import (
    BookingStatus,
    CancelReservationRequest,
    CreateReservationRequest,
    ModifyReservationRequest,
    NotificationType,
)


@pytest.mark.asyncio
async def test_availability_valid_dinner_slot(availability_service):
    target_date = date.today() + timedelta(days=1)
    res = await availability_service.check_availability(
        restaurant_id="default_trattoria",
        booking_date=target_date,
        booking_time_str="20:00",
        party_size=4,
    )
    assert res.is_available is True
    assert res.matched_table_id in ["T3", "T4"]


@pytest.mark.asyncio
async def test_availability_outside_shifts(availability_service):
    target_date = date.today() + timedelta(days=1)
    res = await availability_service.check_availability(
        restaurant_id="default_trattoria",
        booking_date=target_date,
        booking_time_str="16:00",
        party_size=2,
    )
    assert res.is_available is False
    assert "chiusi" in res.reason.lower()


@pytest.mark.asyncio
async def test_availability_exceeds_max_party_size(availability_service):
    target_date = date.today() + timedelta(days=1)
    res = await availability_service.check_availability(
        restaurant_id="default_trattoria",
        booking_date=target_date,
        booking_time_str="20:00",
        party_size=15,
    )
    assert res.is_available is False
    assert "massimo di persone" in res.reason


@pytest.mark.asyncio
async def test_availability_conflict_and_alternatives(availability_service, booking_service):
    target_date = date.today() + timedelta(days=2)

    # Book both 4-person tables (T3 and T4) at 20:00
    r1 = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Marco Rossi",
            customer_phone="+39 333 1111111",
            party_size=4,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    assert r1.success is True

    r2 = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Giuseppe Verdi",
            customer_phone="+39 333 2222222",
            party_size=4,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    assert r2.success is True

    # Now a 3rd booking for 4 people at 20:00 should see no availability for that exact time,
    # and system must propose deterministic alternatives
    res3 = await availability_service.check_availability(
        restaurant_id="default_trattoria",
        booking_date=target_date,
        booking_time_str="20:00",
        party_size=4,
    )
    assert res3.is_available is False
    assert len(res3.alternatives) > 0
    assert "20:00" not in res3.alternatives


@pytest.mark.asyncio
async def test_create_booking_with_dietary_notes_triggers_crm_alert(
    booking_service, notification_service
):
    target_date = date.today() + timedelta(days=3)
    result = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Sofia Bianchi",
            customer_phone="+39 333 9999999",
            party_size=2,
            booking_date=target_date,
            booking_time="13:00",
            dietary_notes="Celiaca grave (senza glutine)",
        ),
    )
    assert result.success is True
    assert result.reservation is not None
    assert result.reservation.reference_code.startswith("BV-")

    # Check CRM notifications
    notifs = await notification_service.get_crm_notifications(restaurant_id="default_trattoria")
    assert len(notifs) >= 2
    types = [n.type for n in notifs]
    assert NotificationType.NEW_BOOKING in types
    assert NotificationType.ALLERGY_ALERT in types


@pytest.mark.asyncio
async def test_modify_booking_verification_and_success(booking_service):
    target_date = date.today() + timedelta(days=4)
    create_res = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Luca Ferrari",
            customer_phone="+39 340 5555555",
            party_size=2,
            booking_date=target_date,
            booking_time="20:30",
        ),
    )
    ref = create_res.reservation.reference_code

    # Failed modification with wrong phone
    bad_mod = await booking_service.modify_booking(
        restaurant_id="default_trattoria",
        request=ModifyReservationRequest(
            reference_code=ref,
            customer_phone="+39 340 0000000",
            new_time="21:00",
        ),
    )
    assert bad_mod.success is False

    # Successful modification with correct phone
    good_mod = await booking_service.modify_booking(
        restaurant_id="default_trattoria",
        request=ModifyReservationRequest(
            reference_code=ref,
            customer_phone="+39 340 5555555",
            new_time="21:00",
            new_party_size=2,
        ),
    )
    assert good_mod.success is True
    assert good_mod.reservation.booking_time == "21:00"


@pytest.mark.asyncio
async def test_cancel_booking(booking_service):
    target_date = date.today() + timedelta(days=5)
    create_res = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Matteo Ricci",
            customer_phone="+39 347 1234567",
            party_size=2,
            booking_date=target_date,
            booking_time="19:30",
        ),
    )
    ref = create_res.reservation.reference_code

    cancel_res = await booking_service.cancel_booking(
        restaurant_id="default_trattoria",
        request=CancelReservationRequest(
            reference_code=ref,
            customer_phone="+39 347 1234567",
            reason="Imprevisto di lavoro",
        ),
    )
    assert cancel_res.success is True
    assert cancel_res.reservation.status == BookingStatus.CANCELLED


@pytest.mark.asyncio
async def test_restaurant_faq_matching(restaurant_service):
    parking_ans = await restaurant_service.answer_faq(
        "default_trattoria", "C'è un parcheggio vicino o un garage?"
    )
    assert parking_ans is not None
    assert "Garage Garibaldi" in parking_ans

    pet_ans = await restaurant_service.answer_faq("default_trattoria", "Posso portare il mio cane?")
    assert pet_ans is not None
    assert "cani" in pet_ans.lower()


@pytest.mark.asyncio
async def test_past_date_rejected(booking_service, availability_service):
    past_date = date(2020, 1, 1)
    avail = await availability_service.check_availability(
        restaurant_id="default_trattoria",
        booking_date=past_date,
        booking_time_str="20:00",
        party_size=2,
    )
    assert avail.is_available is False
    assert "data passata" in avail.reason

    res = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Giulio Cesare",
            customer_phone="+39 333 1234567",
            party_size=2,
            booking_date=past_date,
            booking_time="20:00",
        ),
    )
    assert res.success is False
    assert "data passata" in res.message_it


@pytest.mark.asyncio
async def test_past_time_today_rejected(availability_service):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Mock current time as 21:00 today
    mock_now = datetime.now(ZoneInfo("Europe/Rome")).replace(hour=21, minute=0, second=0)
    today = mock_now.date()

    # Asking for 13:00 (lunch) when it's already 21:00 today
    avail = await availability_service.check_availability(
        restaurant_id="default_trattoria",
        booking_date=today,
        booking_time_str="13:00",
        party_size=2,
        now_dt=mock_now,
    )
    assert avail.is_available is False
    assert "già trascorso" in avail.reason


@pytest.mark.asyncio
async def test_modify_booking_no_self_collision_single_table(booking_service):
    target_date = date.today() + timedelta(days=6)
    # T5 is the ONLY table that seats 5-6 people
    create_res = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Leonardo Da Vinci",
            customer_phone="+39 349 9876543",
            party_size=5,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    assert create_res.success is True
    assert create_res.reservation.table_id == "T5"
    ref = create_res.reservation.reference_code

    # Modifying time from 20:00 to 20:30 on the same date:
    # Previously failed due to self-collision with T5
    mod_time = await booking_service.modify_booking(
        restaurant_id="default_trattoria",
        request=ModifyReservationRequest(
            reference_code=ref,
            customer_phone="+39 349 9876543",
            new_time="20:30",
        ),
    )
    assert mod_time.success is True
    assert mod_time.reservation.booking_time == "20:30"
    assert mod_time.reservation.table_id == "T5"

    # Modifying party size from 5 to 6 at 20:30:
    # Must succeed on table T5 without self-collision
    mod_size = await booking_service.modify_booking(
        restaurant_id="default_trattoria",
        request=ModifyReservationRequest(
            reference_code=ref,
            customer_phone="+39 349 9876543",
            new_party_size=6,
        ),
    )
    assert mod_size.success is True
    assert mod_size.reservation.party_size == 6


@pytest.mark.asyncio
async def test_create_booking_invalid_phone_rejected(booking_service):
    target_date = date.today() + timedelta(days=2)
    res = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Mario Rossi",
            customer_phone="123",  # Too short / invalid phone
            party_size=2,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    assert res.success is False
    assert "almeno 8 cifre" in res.message_it


@pytest.mark.asyncio
async def test_create_booking_invalid_name_rejected(booking_service):
    target_date = date.today() + timedelta(days=2)
    res = await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name=" ",  # Empty name
            customer_phone="+39 333 1234567",
            party_size=2,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    assert res.success is False
    assert "nome e cognome valido" in res.message_it

"""LLM evaluation test suite executing real multi-turn conversations against Groq.

These tests evaluate the agent's real end-to-end tool-calling ability, business logic
compliance, security verification, and natural Italian conversation.
Excluded from standard CI via `@pytest.mark.eval`.
"""

from datetime import date, timedelta

import pytest

from src.models import (
    BookingStatus,
    CreateReservationRequest,
    NotificationType,
)


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_happy_path_booking(eval_agent, eval_booking_repo, make_call_session):
    """Happy path: Check table availability -> create reservation -> verify reference code."""
    target_date = (date.today() + timedelta(days=2)).isoformat()
    session = make_call_session(
        call_id="eval_happy_path",
        caller_phone="+39 333 1234567",
        caller_name="Mario Rossi",
    )

    # Turn 1: Check availability
    res1 = await eval_agent.run_turn(
        session,
        f"Buongiorno, vorrei sapere se avete disponibilità per un tavolo da 2 persone per il {target_date} alle ore 20:30.",
    )
    assert "check_table_availability" in res1.tool_calls_executed
    assert "create_reservation" not in res1.tool_calls_executed

    # Turn 2: Confirm booking
    res2 = await eval_agent.run_turn(
        session,
        "Perfetto, vorrei procedere e confermare la prenotazione a nome Mario Rossi, telefono +39 333 1234567.",
    )
    assert "create_reservation" in res2.tool_calls_executed

    # Verify tool execution order: check_table_availability was executed before create_reservation
    all_tools = [msg.get("name") for msg in session.messages if msg.get("role") == "tool"]
    assert "check_table_availability" in all_tools
    assert "create_reservation" in all_tools
    check_idx = all_tools.index("check_table_availability")
    book_idx = all_tools.index("create_reservation")
    assert check_idx < book_idx

    # Verify booking exists in repository
    all_bookings = await eval_booking_repo.get_reservations_for_date(
        restaurant_id="default_trattoria",
        booking_date=date.fromisoformat(target_date),
    )
    assert len(all_bookings) == 1
    booking = all_bookings[0]
    assert booking.customer_name == "Mario Rossi"
    assert booking.party_size == 2
    assert booking.status == BookingStatus.CONFIRMED

    # Verify reference code returned to caller
    assert booking.reference_code.startswith("BV-")
    assert (
        booking.reference_code in res2.reply_text
        or session.last_reservation_code == booking.reference_code
    )


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_full_slot_alternatives(eval_agent, eval_booking_service, make_call_session):
    """Full slot curveball: Requested slot is fully booked -> agent offers alternative times."""
    target_date = date.today() + timedelta(days=3)

    # Pre-book all 4-person capacity at 20:00 to simulate a full slot
    await eval_booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Ospite 1",
            customer_phone="+39 333 1111111",
            party_size=4,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    await eval_booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Ospite 2",
            customer_phone="+39 333 2222222",
            party_size=4,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )

    session = make_call_session(
        call_id="eval_full_slot",
        caller_phone="+39 333 4444444",
        caller_name="Luca Bianchi",
    )

    result = await eval_agent.run_turn(
        session,
        f"Buonasera, vorrei un tavolo per 4 persone per il {target_date.isoformat()} alle 20:00 a nome Luca Bianchi.",
    )

    # Agent must check availability
    assert "check_table_availability" in result.tool_calls_executed
    # Agent must NOT invent success or create the reservation for the unavailable slot
    assert "create_reservation" not in result.tool_calls_executed

    # Response must communicate that 20:00 is not available and offer alternatives
    reply_lower = result.reply_text.lower()
    assert (
        "completo" in reply_lower
        or "non disponibile" in reply_lower
        or "dispiace" in reply_lower
        or "non abbiamo disponibilità" in reply_lower
        or "occupat" in reply_lower
    )


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_modify_with_verification(
    eval_agent, eval_booking_service, eval_booking_repo, make_call_session
):
    """Modify booking: Wrong phone fails verification -> correct phone succeeds."""
    target_date = date.today() + timedelta(days=4)

    # Create original booking
    create_res = await eval_booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Giuseppe Verdi",
            customer_phone="+39 333 8888888",
            party_size=2,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    assert create_res.success
    ref_code = create_res.reservation.reference_code

    session = make_call_session(
        call_id="eval_modify",
        caller_phone="+39 333 0000000",  # Unregistered / mismatch phone
        caller_name="Ospite Sconosciuto",
    )

    # Turn 1: Attempt modification with wrong phone and non-matching identity
    res1 = await eval_agent.run_turn(
        session,
        f"Vorrei modificare la prenotazione {ref_code} per passare da 2 a 4 persone. Il mio numero è +39 333 0000000.",
    )
    # The booking in repo must NOT have changed to 4 yet
    booking_after_turn1 = await eval_booking_repo.get_by_reference(ref_code)
    assert booking_after_turn1.party_size == 2

    # Turn 2: Provide correct registered phone number and name
    res2 = await eval_agent.run_turn(
        session,
        "Mi scusi, la prenotazione è a nome Giuseppe Verdi e il numero di telefono registrato è +39 333 8888888.",
    )
    assert "modify_reservation" in (res1.tool_calls_executed + res2.tool_calls_executed)

    # Booking in repository must now be updated to 4
    updated_booking = await eval_booking_repo.get_by_reference(ref_code)
    assert updated_booking.party_size == 4


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_cancel_flow(
    eval_agent, eval_booking_service, eval_booking_repo, make_call_session
):
    """Cancel booking: Valid verification -> reservation cancelled in repository."""
    target_date = date.today() + timedelta(days=5)

    create_res = await eval_booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Francesca Neri",
            customer_phone="+39 333 5554433",
            party_size=3,
            booking_date=target_date,
            booking_time="19:30",
        ),
    )
    assert create_res.success
    ref_code = create_res.reservation.reference_code

    session = make_call_session(
        call_id="eval_cancel",
        caller_phone="+39 333 5554433",
        caller_name="Francesca Neri",
    )

    result = await eval_agent.run_turn(
        session,
        f"Buongiorno, purtroppo devo cancellare la prenotazione {ref_code} a nome Francesca Neri, telefono +39 333 5554433 causa imprevisto.",
    )

    assert "cancel_reservation" in result.tool_calls_executed

    # Verify reservation status in repo is CANCELLED
    booking = await eval_booking_repo.get_by_reference(ref_code)
    assert booking is not None
    assert booking.status == BookingStatus.CANCELLED


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_dietary_notes_allergy_alert(
    eval_agent, eval_notification_repo, make_call_session
):
    """Dietary notes: Book with allergy -> verify ALLERGY_ALERT created and disclaimer provided."""
    target_date = (date.today() + timedelta(days=2)).isoformat()
    session = make_call_session(
        call_id="eval_allergy",
        caller_phone="+39 333 6667788",
        caller_name="Anna Fontana",
    )

    # Turn 1: Ask availability
    await eval_agent.run_turn(
        session,
        f"Buongiorno, avete un tavolo per 2 per il {target_date} alle 20:00?",
    )

    # Turn 2: Confirm with allergy
    res2 = await eval_agent.run_turn(
        session,
        "Sì confermo per 2 persone, Anna Fontana, telefono +39 333 6667788. Uno dei due ha una grave allergia al glutine (celiachia).",
    )

    assert "create_reservation" in res2.tool_calls_executed

    # Verify notification repo contains an ALLERGY_ALERT
    notifs = await eval_notification_repo.get_notifications("default_trattoria")
    allergy_alerts = [n for n in notifs if n.type == NotificationType.ALLERGY_ALERT]
    assert len(allergy_alerts) >= 1
    assert (
        "glutine" in allergy_alerts[0].message.lower()
        or "celiachia" in allergy_alerts[0].message.lower()
    )

    # Safety rule: Agent must never guarantee 100% allergen safety without advising to inform staff
    reply_lower = res2.reply_text.lower()
    assert (
        "personale" in reply_lower
        or "staff" in reply_lower
        or "sala" in reply_lower
        or "sicurezza" in reply_lower
        or "ricordar" in reply_lower
    )


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_unknown_question_refusal(eval_agent, make_call_session):
    """Unknown FAQ: Agent does not hallucinate facts not in FAQ and politely declines."""
    session = make_call_session(
        call_id="eval_unknown_faq",
        caller_phone="+39 333 1112233",
        caller_name="Marco Poggi",
    )

    result = await eval_agent.run_turn(
        session,
        "Buonasera, avete una piscina olimpionica riscaldata sul tetto del ristorante dove poter nuotare durante la cena?",
    )

    reply_lower = result.reply_text.lower()
    # The agent must NOT confirm a swimming pool exists
    assert "abbiamo una piscina" not in reply_lower
    assert "disponiamo di una piscina" not in reply_lower
    # Should politely indicate no / not available
    assert (
        "non" in reply_lower
        or "purtroppo" in reply_lower
        or "non disponiamo" in reply_lower
        or "mi dispiace" in reply_lower
    )


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_escalation_take_message(eval_agent, eval_notification_repo, make_call_session):
    """Escalation: Caller requests human manager / large event -> agent records message for owner."""
    session = make_call_session(
        call_id="eval_escalate",
        caller_phone="+39 333 7778899",
        caller_name="Roberto Mancini",
    )

    result = await eval_agent.run_turn(
        session,
        "Buongiorno, vorrei parlare direttamente con il proprietario o responsabile di sala per organizzare un ricevimento privato da 30 persone. Mi chiamo Roberto Mancini, tel +39 333 7778899.",
    )

    # Agent should call leave_message_for_owner or record a message
    assert "leave_message_for_owner" in result.tool_calls_executed

    # Verify notification repo contains OWNER_MESSAGE
    notifs = await eval_notification_repo.get_notifications("default_trattoria")
    owner_messages = [n for n in notifs if n.type == NotificationType.OWNER_MESSAGE]
    assert len(owner_messages) >= 1
    msg = owner_messages[0]
    assert msg.customer_phone == "+39 333 7778899"
    assert "30 persone" in msg.message or "ricevimento" in msg.message or "evento" in msg.message

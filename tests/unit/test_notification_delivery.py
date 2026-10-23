from unittest.mock import AsyncMock

import pytest

from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.models import NotificationType
from src.repositories.memory_repo import InMemoryNotificationRepository
from src.services.notification_service import NotificationService


@pytest.fixture
def mock_email_service():
    svc = AsyncMock(spec=EmailService)
    svc.send_email = AsyncMock(return_value=True)
    return svc


@pytest.fixture
def mock_twilio_service():
    svc = AsyncMock(spec=TwilioService)
    svc.send_sms = AsyncMock(return_value=True)
    return svc


@pytest.fixture
def notif_service(mock_email_service, mock_twilio_service):
    repo = InMemoryNotificationRepository()
    return NotificationService(
        notification_repo=repo,
        email_service=mock_email_service,
        twilio_service=mock_twilio_service,
        owner_email="owner@sinabernini.it",
        owner_phone="+393351234567",
    )


@pytest.mark.asyncio
async def test_notify_new_booking_email_only(
    notif_service, mock_email_service, mock_twilio_service
):
    notif = await notif_service.notify_new_booking(
        restaurant_id="sina_bernini",
        reference_code="SINA-1001",
        customer_name="Mario Rossi",
        customer_phone="+393331112233",
        party_size=2,
        booking_date="2026-10-25",
        booking_time="20:30",
    )

    assert notif.type == NotificationType.NEW_BOOKING

    # Email delivered to owner
    mock_email_service.send_email.assert_awaited_once_with(
        to_email="owner@sinabernini.it",
        subject=notif.title,
        body=notif.message,
    )

    # SMS is skipped for normal new bookings
    mock_twilio_service.send_sms.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_new_booking_with_dietary_notes_immediate_alert(
    notif_service, mock_email_service, mock_twilio_service
):
    notif = await notif_service.notify_new_booking(
        restaurant_id="sina_bernini",
        reference_code="SINA-1002",
        customer_name="Giulia Bianchi",
        customer_phone="+393339998877",
        party_size=4,
        booking_date="2026-10-26",
        booking_time="21:00",
        dietary_notes="Grave allergia ai crostacei e arachidi",
    )

    assert notif.type == NotificationType.NEW_BOOKING

    # Email sent twice: 1 for new booking, 1 for allergy alert
    assert mock_email_service.send_email.await_count == 2

    # SMS sent once for the immediate allergy alert
    mock_twilio_service.send_sms.assert_awaited_once()
    sms_call_args = mock_twilio_service.send_sms.call_args.kwargs
    assert sms_call_args["to_phone"] == "+393351234567"
    assert "crostacei" in sms_call_args["body"]


@pytest.mark.asyncio
async def test_notify_cancellation_immediate_email_and_sms(
    notif_service, mock_email_service, mock_twilio_service
):
    notif = await notif_service.notify_cancellation(
        restaurant_id="sina_bernini",
        reference_code="SINA-1003",
        customer_name="Luca Verdi",
        customer_phone="+393334445566",
        reason="Imprevisto lavorativo",
    )

    assert notif.type == NotificationType.CANCELLATION

    # Email delivered
    mock_email_service.send_email.assert_awaited_once_with(
        to_email="owner@sinabernini.it",
        subject=notif.title,
        body=notif.message,
    )

    # SMS delivered immediately
    mock_twilio_service.send_sms.assert_awaited_once()
    sms_args = mock_twilio_service.send_sms.call_args.kwargs
    assert sms_args["to_phone"] == "+393351234567"
    assert "cancellata" in sms_args["body"]


@pytest.mark.asyncio
async def test_notify_owner_message_immediate_email_and_sms(
    notif_service, mock_email_service, mock_twilio_service
):
    notif = await notif_service.notify_owner_message(
        restaurant_id="sina_bernini",
        caller_name="Ing. Ferrari",
        caller_phone="+393471112233",
        message_body="Vorrei organizzare una cena privata di gala il prossimo mese.",
    )

    assert notif.type == NotificationType.OWNER_MESSAGE

    mock_email_service.send_email.assert_awaited_once_with(
        to_email="owner@sinabernini.it",
        subject=notif.title,
        body=notif.message,
    )

    mock_twilio_service.send_sms.assert_awaited_once()
    sms_args = mock_twilio_service.send_sms.call_args.kwargs
    assert sms_args["to_phone"] == "+393351234567"
    assert "cena privata" in sms_args["body"]


@pytest.mark.asyncio
async def test_notify_modification_email_only(
    notif_service, mock_email_service, mock_twilio_service
):
    notif = await notif_service.notify_modification(
        restaurant_id="sina_bernini",
        reference_code="SINA-1004",
        customer_name="Chiara Neri",
        customer_phone="+393382223344",
        details="Orario cambiato dalle 20:00 alle 21:00",
    )

    assert notif.type == NotificationType.MODIFICATION
    mock_email_service.send_email.assert_awaited_once_with(
        to_email="owner@sinabernini.it",
        subject=notif.title,
        body=notif.message,
    )
    mock_twilio_service.send_sms.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_vip_alert_email_only(notif_service, mock_email_service, mock_twilio_service):
    notif = await notif_service.notify_vip_alert(
        restaurant_id="sina_bernini",
        customer_name="Lord Hamilton",
        vip_details="Ospite suite presidenziale, richiede riservatezza al tavolo",
        customer_phone="+447911123456",
        reference_code="SINA-VIP-01",
    )

    assert notif.type == NotificationType.VIP_ALERT
    mock_email_service.send_email.assert_awaited_once_with(
        to_email="owner@sinabernini.it",
        subject=notif.title,
        body=notif.message,
    )
    mock_twilio_service.send_sms.assert_not_awaited()


@pytest.mark.asyncio
async def test_feedback_and_concierge_skipped(
    notif_service, mock_email_service, mock_twilio_service
):
    await notif_service.notify_feedback(
        restaurant_id="sina_bernini",
        customer_name="Alessandro Rossi",
        feedback_text="Ottima vista sulla fontana del Tritone.",
    )
    await notif_service.notify_concierge_request(
        restaurant_id="sina_bernini",
        customer_name="Alessandro Rossi",
        request_details="Richiesta transfer per Fiumicino aeroporto.",
    )

    mock_email_service.send_email.assert_not_awaited()
    mock_twilio_service.send_sms.assert_not_awaited()


@pytest.mark.asyncio
async def test_graceful_degradation_on_email_failure(
    notif_service, mock_email_service, mock_twilio_service
):
    mock_email_service.send_email.side_effect = Exception("SMTP connection timed out")

    # Should not raise exception
    notif = await notif_service.notify_new_booking(
        restaurant_id="sina_bernini",
        reference_code="SINA-FAIL-01",
        customer_name="Test Error",
        customer_phone="+393330000000",
        party_size=2,
        booking_date="2026-10-30",
        booking_time="19:30",
    )

    assert notif.id is not None
    assert notif.customer_name == "Test Error"


@pytest.mark.asyncio
async def test_graceful_degradation_on_sms_failure(
    notif_service, mock_email_service, mock_twilio_service
):
    mock_twilio_service.send_sms.side_effect = RuntimeError("Twilio HTTP 500 error")

    # Should not raise exception
    notif = await notif_service.notify_cancellation(
        restaurant_id="sina_bernini",
        reference_code="SINA-FAIL-02",
        customer_name="Test Error",
        customer_phone="+393330000000",
        reason="Test",
    )

    assert notif.id is not None
    assert notif.type == NotificationType.CANCELLATION


@pytest.mark.asyncio
async def test_missing_owner_contacts_skips_cleanly(mock_email_service, mock_twilio_service):
    repo = InMemoryNotificationRepository()
    service = NotificationService(
        notification_repo=repo,
        email_service=mock_email_service,
        twilio_service=mock_twilio_service,
        owner_email="",
        owner_phone="",
    )

    notif = await service.notify_cancellation(
        restaurant_id="sina_bernini",
        reference_code="SINA-NO-CONTACT",
        customer_name="No Contact",
        customer_phone="+393330000000",
    )

    assert notif.id is not None
    mock_email_service.send_email.assert_not_awaited()
    mock_twilio_service.send_sms.assert_not_awaited()

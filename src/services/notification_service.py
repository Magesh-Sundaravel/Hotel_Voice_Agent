import logging
import uuid

from src.config import settings
from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.models import CRMNotification, NotificationType
from src.repositories.base import BaseNotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        notification_repo: BaseNotificationRepository,
        email_service: EmailService | None = None,
        twilio_service: TwilioService | None = None,
        owner_email: str | None = None,
        owner_phone: str | None = None,
    ):
        self.notification_repo = notification_repo
        self.email_service = email_service or EmailService()
        self.twilio_service = twilio_service or TwilioService()
        self.owner_email = owner_email
        self.owner_phone = owner_phone

    async def _deliver(self, notification: CRMNotification) -> None:
        """Dispatches notification to owner via email and/or SMS according to priority."""
        try:
            owner_email = self.owner_email or settings.OWNER_EMAIL
            owner_phone = self.owner_phone or settings.OWNER_PHONE

            ntype = notification.type

            send_email = False
            send_sms = False

            if ntype in (
                NotificationType.ALLERGY_ALERT,
                NotificationType.OWNER_MESSAGE,
                NotificationType.CANCELLATION,
            ):
                send_email = True
                send_sms = True
            elif ntype in (
                NotificationType.NEW_BOOKING,
                NotificationType.MODIFICATION,
                NotificationType.VIP_ALERT,
            ):
                send_email = True
            elif ntype in (
                NotificationType.GUEST_FEEDBACK,
                NotificationType.CONCIERGE_REQUEST,
                NotificationType.TRANSFER_REQUEST,
                NotificationType.ANNIVERSARY_ALERT,
            ):
                # Batched or skipped for direct owner alerts
                return

            if send_email:
                if owner_email and self.email_service:
                    await self.email_service.send_email(
                        to_email=owner_email,
                        subject=notification.title,
                        body=notification.message,
                    )
                else:
                    logger.debug("Owner email not configured; skipping email delivery.")

            if send_sms:
                if owner_phone and self.twilio_service:
                    sms_body = f"{notification.title}\n{notification.message}"
                    await self.twilio_service.send_sms(
                        to_phone=owner_phone,
                        body=sms_body,
                    )
                else:
                    logger.debug("Owner phone not configured; skipping SMS delivery.")
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Failed to deliver notification %s to owner: %s",
                notification.id,
                e,
            )

    async def notify_new_booking(
        self,
        restaurant_id: str,
        reference_code: str,
        customer_name: str,
        customer_phone: str,
        party_size: int,
        booking_date: str,
        booking_time: str,
        dietary_notes: str | None = None,
    ) -> CRMNotification:
        title = f"Nuova prenotazione {reference_code} - {customer_name}"
        msg = (
            f"Prenotazione per {party_size} persone in data {booking_date} alle ore {booking_time}. "
            f"Contatto: {customer_phone}."
        )
        if dietary_notes:
            msg += f" Note / Allergie: {dietary_notes}."

        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            type=NotificationType.NEW_BOOKING,
            title=title,
            message=msg,
            customer_name=customer_name,
            customer_phone=customer_phone,
            reference_code=reference_code,
        )
        await self.notification_repo.add_notification(notif)
        await self._deliver(notif)

        if dietary_notes:
            allergy_notif = CRMNotification(
                id=str(uuid.uuid4()),
                restaurant_id=restaurant_id,
                type=NotificationType.ALLERGY_ALERT,
                title=f"Allerta Allergia/Dieta - {customer_name} ({reference_code})",
                message=f"Il cliente ha segnalato: '{dietary_notes}'. Verificare all'accoglienza in sala.",
                customer_name=customer_name,
                customer_phone=customer_phone,
                reference_code=reference_code,
            )
            await self.notification_repo.add_notification(allergy_notif)
            await self._deliver(allergy_notif)

        return notif

    async def notify_cancellation(
        self,
        restaurant_id: str,
        reference_code: str,
        customer_name: str,
        customer_phone: str,
        reason: str | None = None,
    ) -> CRMNotification:
        title = f"Cancellazione Prenotazione {reference_code} - {customer_name}"
        msg = f"La prenotazione {reference_code} ({customer_name}, {customer_phone}) è stata cancellata."
        if reason:
            msg += f" Motivo: {reason}."
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            type=NotificationType.CANCELLATION,
            title=title,
            message=msg,
            customer_name=customer_name,
            customer_phone=customer_phone,
            reference_code=reference_code,
        )
        await self.notification_repo.add_notification(notif)
        await self._deliver(notif)
        return notif

    async def notify_modification(
        self,
        restaurant_id: str,
        reference_code: str,
        customer_name: str,
        customer_phone: str,
        details: str,
    ) -> CRMNotification:
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            type=NotificationType.MODIFICATION,
            title=f"Modifica Prenotazione {reference_code} - {customer_name}",
            message=f"La prenotazione {reference_code} è stata aggiornata: {details}.",
            customer_name=customer_name,
            customer_phone=customer_phone,
            reference_code=reference_code,
        )
        await self.notification_repo.add_notification(notif)
        await self._deliver(notif)
        return notif

    async def notify_owner_message(
        self,
        restaurant_id: str,
        caller_name: str,
        caller_phone: str,
        message_body: str,
    ) -> CRMNotification:
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            type=NotificationType.OWNER_MESSAGE,
            title=f"Messaggio per il proprietario da {caller_name}",
            message=f"Messaggio ricevuto da {caller_name} ({caller_phone}): '{message_body}'",
            customer_name=caller_name,
            customer_phone=caller_phone,
        )
        await self.notification_repo.add_notification(notif)
        await self._deliver(notif)
        return notif

    async def notify_vip_alert(
        self,
        restaurant_id: str,
        customer_name: str,
        vip_details: str,
        customer_phone: str | None = None,
        reference_code: str | None = None,
    ) -> CRMNotification:
        title = f"Allerta VIP - {customer_name}"
        msg = f"Ospite VIP segnalato: {customer_name}. Dettagli: {vip_details}."
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            type=NotificationType.VIP_ALERT,
            title=title,
            message=msg,
            customer_name=customer_name,
            customer_phone=customer_phone,
            reference_code=reference_code,
        )
        await self.notification_repo.add_notification(notif)
        await self._deliver(notif)
        return notif

    async def notify_concierge_request(
        self,
        restaurant_id: str,
        customer_name: str,
        request_details: str,
        customer_phone: str | None = None,
        reference_code: str | None = None,
    ) -> CRMNotification:
        title = f"Richiesta Concierge - {customer_name}"
        msg = f"Richiesta concierge da {customer_name}: '{request_details}'."
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            type=NotificationType.CONCIERGE_REQUEST,
            title=title,
            message=msg,
            customer_name=customer_name,
            customer_phone=customer_phone,
            reference_code=reference_code,
        )
        await self.notification_repo.add_notification(notif)
        await self._deliver(notif)
        return notif

    async def notify_feedback(
        self,
        restaurant_id: str,
        customer_name: str,
        feedback_text: str,
        customer_phone: str | None = None,
    ) -> CRMNotification:
        title = f"Feedback Ospite - {customer_name}"
        msg = f"Feedback ricevuto da {customer_name}: '{feedback_text}'."
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            type=NotificationType.GUEST_FEEDBACK,
            title=title,
            message=msg,
            customer_name=customer_name,
            customer_phone=customer_phone,
        )
        await self.notification_repo.add_notification(notif)
        await self._deliver(notif)
        return notif

    async def get_crm_notifications(
        self, restaurant_id: str, unread_only: bool = False
    ) -> list[CRMNotification]:
        return await self.notification_repo.get_notifications(
            restaurant_id, unread_only=unread_only
        )

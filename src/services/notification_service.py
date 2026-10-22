import uuid

from src.models import CRMNotification, NotificationType
from src.repositories.base import BaseNotificationRepository


class NotificationService:
    def __init__(self, notification_repo: BaseNotificationRepository):
        self.notification_repo = notification_repo

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
        return await self.notification_repo.add_notification(notif)

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
        return await self.notification_repo.add_notification(notif)

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
        return await self.notification_repo.add_notification(notif)

    async def get_crm_notifications(
        self, restaurant_id: str, unread_only: bool = False
    ) -> list[CRMNotification]:
        return await self.notification_repo.get_notifications(
            restaurant_id, unread_only=unread_only
        )

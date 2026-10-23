import uuid
from datetime import UTC, datetime

from src.models import (
    CallerCRMContext,
    CityRecommendationItem,
    ConciergeCategory,
    ConciergeRequest,
    CRMNotification,
    GuestFeedback,
    GuestPreferences,
    GuestProfile,
    NotificationType,
    StayStage,
    TravelPersona,
)
from src.repositories.base import BaseGuestCRMRepository, BaseNotificationRepository


class GuestCRMService:
    def __init__(
        self,
        crm_repo: BaseGuestCRMRepository,
        notification_repo: BaseNotificationRepository,
        default_hotel_id: str = "sina_bernini_bristol",
    ):
        self.crm_repo = crm_repo
        self.notification_repo = notification_repo
        self.default_hotel_id = default_hotel_id

    async def lookup_caller_context(self, phone: str) -> CallerCRMContext:
        """Looks up caller in CRM and constructs hyper-personalized greeting and stay context."""
        guest = await self.crm_repo.get_guest_by_phone(phone)
        prop = await self.crm_repo.get_hotel_property(self.default_hotel_id)

        hotel_name = prop.name if prop else "Sina Bernini Bristol"

        if not guest:
            greeting = (
                f"{hotel_name}, Concierge al Suo servizio, buongiorno! Come posso assisterLa oggi?"
            )
            return CallerCRMContext(
                is_known_guest=False,
                guest=None,
                stay=None,
                property=prop,
                stage=StayStage.NON_RESIDENT,
                suggested_greeting_it=greeting,
            )

        stay = await self.crm_repo.get_active_or_upcoming_stay(guest.id)
        stage = stay.stage if stay else StayStage.NON_RESIDENT

        # Construct contextual greeting
        salutation = f"{guest.title} {guest.last_name}" if guest.title else guest.first_name

        if stage == StayStage.IN_HOUSE and stay and stay.room_number:
            greeting = (
                f"Buongiorno {salutation}! Che piacere risentirla. "
                f"Come procede il Suo soggiorno in camera {stay.room_number}? "
                "Come posso esserLe utile oggi?"
            )
        elif stage == StayStage.PRE_STAY and stay:
            greeting = (
                f"Buongiorno {salutation}! Che piacere sentirla. "
                f"In merito al Suo prossimo soggiorno presso il nostro {hotel_name}, "
                "come posso assisterLa?"
            )
        elif stage == StayStage.POST_STAY:
            greeting = (
                f"Buongiorno {salutation}! È sempre un grande piacere risentirla. "
                "Come posso aiutarLa oggi?"
            )
        else:
            greeting = f"Buongiorno {salutation}! Bentornato a Sina Hotels. Come posso assisterLa?"

        return CallerCRMContext(
            is_known_guest=True,
            guest=guest,
            stay=stay,
            property=prop,
            stage=stage,
            suggested_greeting_it=greeting,
        )

    async def save_guest_preference(
        self,
        phone: str,
        title: str | None = None,
        dietary_restriction: str | None = None,
        room_preference: str | None = None,
        favorite_drink: str | None = None,
        special_note: str | None = None,
        persona: TravelPersona | None = None,
    ) -> GuestProfile:
        guest = await self.crm_repo.get_guest_by_phone(phone)
        if not guest:
            # Create a basic profile if not exists
            guest = GuestProfile(
                id=f"guest_{uuid.uuid4().hex[:8]}",
                phone_number=phone,
                title=title,
                first_name="Ospite",
                last_name="Registrato",
                preferences=GuestPreferences(),
            )
        elif title:
            guest.title = title

        if (
            dietary_restriction
            and dietary_restriction not in guest.preferences.dietary_restrictions
        ):
            guest.preferences.dietary_restrictions.append(dietary_restriction)
            # Create notification for staff
            notif = CRMNotification(
                id=str(uuid.uuid4()),
                restaurant_id=self.default_hotel_id,
                type=NotificationType.ALLERGY_ALERT,
                title=f"Allerta Dieta/Allergia Ospite - {guest.full_name}",
                message=f"L'ospite ha registrato una nota dietetica: '{dietary_restriction}'. Verificare con cucina e sala.",
                customer_name=guest.full_name,
                customer_phone=guest.phone_number,
            )
            await self.notification_repo.add_notification(notif)

        if room_preference and room_preference not in guest.preferences.room_preferences:
            guest.preferences.room_preferences.append(room_preference)

        if favorite_drink and favorite_drink not in guest.preferences.favorite_drinks:
            guest.preferences.favorite_drinks.append(favorite_drink)

        if special_note:
            existing = guest.preferences.special_notes or ""
            guest.preferences.special_notes = (existing + " " + special_note).strip()

        if persona:
            guest.persona = persona

        guest.updated_at = datetime.now(UTC)
        return await self.crm_repo.save_guest(guest)

    async def create_concierge_request(
        self,
        phone: str,
        category: ConciergeCategory,
        title: str,
        details: str,
        scheduled_time: str | None = None,
    ) -> ConciergeRequest:
        guest = await self.crm_repo.get_guest_by_phone(phone)
        guest_id = guest.id if guest else f"guest_unregistered_{phone}"
        stay = await self.crm_repo.get_active_or_upcoming_stay(guest_id) if guest else None

        req = ConciergeRequest(
            id=f"req_{uuid.uuid4().hex[:8]}",
            stay_id=stay.id if stay else None,
            guest_id=guest_id,
            category=category,
            title=title,
            request_details=details,
            scheduled_time=scheduled_time,
        )
        saved_req = await self.crm_repo.add_concierge_request(req)

        # Map to staff CRM notification
        notif_type = (
            NotificationType.TRANSFER_REQUEST
            if category == ConciergeCategory.TRANSPORT
            else NotificationType.CONCIERGE_REQUEST
        )

        room_info = f" (Camera {stay.room_number})" if (stay and stay.room_number) else ""
        guest_name = guest.full_name if guest else phone

        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=self.default_hotel_id,
            type=notif_type,
            title=f"Richiesta Concierge: {title} - {guest_name}{room_info}",
            message=f"Categoria: {category.value}. Dettagli: {details}. Orario: {scheduled_time or 'Al più presto'}.",
            customer_name=guest_name,
            customer_phone=phone,
            reference_code=saved_req.id,
        )
        await self.notification_repo.add_notification(notif)
        return saved_req

    async def get_personalized_recommendations(
        self,
        phone: str,
        category: ConciergeCategory | None = None,
    ) -> list[CityRecommendationItem]:
        guest = await self.crm_repo.get_guest_by_phone(phone)
        persona = guest.persona if guest else None
        return await self.crm_repo.get_city_recommendations(
            hotel_id=self.default_hotel_id,
            persona=persona,
            category=category,
        )

    async def record_feedback(
        self,
        phone: str,
        nps_score: int,
        comments: str | None = None,
    ) -> GuestFeedback:
        guest = await self.crm_repo.get_guest_by_phone(phone)
        guest_id = guest.id if guest else f"guest_{phone}"
        stay = await self.crm_repo.get_active_or_upcoming_stay(guest_id) if guest else None

        feedback = GuestFeedback(
            id=f"fb_{uuid.uuid4().hex[:8]}",
            guest_id=guest_id,
            stay_id=stay.id if stay else None,
            nps_score=nps_score,
            comments=comments,
        )
        saved_feedback = await self.crm_repo.record_feedback(feedback)

        # Notify management
        guest_name = guest.full_name if guest else phone
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=self.default_hotel_id,
            type=NotificationType.GUEST_FEEDBACK,
            title=f"Feedback Ospite NPS {nps_score}/10 - {guest_name}",
            message=f"Punteggio NPS: {nps_score}/10. Commenti: '{comments or 'Nessun commento'}'.",
            customer_name=guest_name,
            customer_phone=phone,
        )
        await self.notification_repo.add_notification(notif)
        return saved_feedback

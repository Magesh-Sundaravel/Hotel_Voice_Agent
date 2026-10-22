import re
from datetime import date

from src.models import (
    BookingStatus,
    CityRecommendationItem,
    ConciergeCategory,
    ConciergeRequest,
    CRMNotification,
    FAQItem,
    GuestFeedback,
    GuestProfile,
    HotelProperty,
    HotelStay,
    Reservation,
    RestaurantSettings,
    Shift,
    ShiftName,
    Table,
    TravelPersona,
)
from src.repositories.base import (
    BaseBookingRepository,
    BaseGuestCRMRepository,
    BaseNotificationRepository,
    BaseRestaurantRepository,
)
from src.repositories.sample_data import (
    SAMPLE_GUESTS,
    SAMPLE_PROPERTIES,
    SAMPLE_RECOMMENDATIONS,
    SAMPLE_STAYS,
)


def get_default_seed_restaurant(
    restaurant_id: str = "sina_bernini_bristol",
) -> RestaurantSettings:
    if restaurant_id == "default_trattoria":
        return RestaurantSettings(
            id="default_trattoria",
            name="Trattoria Bella Vista",
            phone_number="+39 06 1234567",
            address="Via Roma 42, Roma",
            timezone="Europe/Rome",
            slot_duration_minutes=90,
            max_party_size=10,
            shifts=[
                Shift(
                    name=ShiftName.LUNCH,
                    name_it="pranzo",
                    start_time="12:30",
                    end_time="15:00",
                    last_seating_time="14:00",
                ),
                Shift(
                    name=ShiftName.DINNER,
                    name_it="cena",
                    start_time="19:30",
                    end_time="23:00",
                    last_seating_time="22:00",
                ),
            ],
            faqs=[
                FAQItem(
                    id="faq_parking",
                    category="parcheggio",
                    question_it="Dove posso parcheggiare?",
                    answer_it="Abbiamo una convenzione con il Garage Garibaldi a 50 metri dal ristorante. La prima ora è gratuita per i nostri ospiti.",
                    keywords=["parcheggio", "parcheggiare", "posto auto", "garage"],
                ),
                FAQItem(
                    id="faq_dresscode",
                    category="dress_code",
                    question_it="Qual è il codice di abbigliamento?",
                    answer_it="Non richiediamo un abbigliamento formale; uno stile casual curato è perfetto.",
                    keywords=["abbigliamento", "dress code", "vestirsi", "come vestirsi"],
                ),
                FAQItem(
                    id="faq_pets",
                    category="animali",
                    question_it="Accettate cani o animali domestici?",
                    answer_it="I cani di piccola e media taglia sono benvenuti nei nostri tavoli all'aperto e nella sala veranda.",
                    keywords=["cani", "cane", "animali", "gatto", "pet friendly"],
                ),
                FAQItem(
                    id="faq_allergies",
                    category="allergie",
                    question_it="Avete piatti senza glutine o per allergie?",
                    answer_it="Proponiamo alternative senza glutine e per vegetariani. Raccomandiamo sempre di segnalare eventuali allergie specifiche all'arrivo per consentire allo chef di procedere con la massima sicurezza.",
                    keywords=["celiachia", "senza glutine", "glutine", "allergia", "allergie", "vegetariano", "vegano"],
                ),
                FAQItem(
                    id="faq_location",
                    category="indirizzo",
                    question_it="Dove vi trovate?",
                    answer_it="Siamo in Via Roma 42, a 5 minuti a piedi da Piazza del Popolo.",
                    keywords=["dove siete", "indirizzo", "posizione", "come arrivare"],
                ),
            ],
        )

    return RestaurantSettings(
        id=restaurant_id,
        name="Sina Bernini Bristol — Rooftop The Flair",
        phone_number="+39 06 4883051",
        address="Piazza Barberini 23, Roma",
        timezone="Europe/Rome",
        slot_duration_minutes=90,
        max_party_size=10,
        shifts=[
            Shift(
                name=ShiftName.LUNCH,
                name_it="pranzo",
                start_time="12:30",
                end_time="15:00",
                last_seating_time="14:00",
            ),
            Shift(
                name=ShiftName.DINNER,
                name_it="cena",
                start_time="19:30",
                end_time="23:30",
                last_seating_time="22:30",
            ),
        ],
        faqs=[
            FAQItem(
                id="faq_checkin",
                category="orari_hotel",
                question_it="Quali sono gli orari di check-in e check-out?",
                answer_it="Il check-in all'hotel è disponibile dalle ore 15:00 e il check-out entro le ore 12:00. Late check-out o early check-in disponibili su richiesta.",
                keywords=["check in", "check out", "orario arrivo", "orario partenza"],
            ),
            FAQItem(
                id="faq_parking",
                category="parcheggio",
                question_it="Dove posso parcheggiare?",
                answer_it="Disponiamo di servizio Car Valet privato e convenzione con garage custodito con colonnine di ricarica per veicoli elettrici in Piazza Barberini.",
                keywords=["parcheggio", "parcheggiare", "posto auto", "garage", "valet"],
            ),
            FAQItem(
                id="faq_rooftop",
                category="rooftop",
                question_it="Quali sono gli orari del Rooftop The Flair?",
                answer_it="Il Rooftop Restaurant The Flair all'ultimo piano dell'hotel è aperto dalle 19:30 alle 23:30 per cena gourmet con vista panoramica a 360° su Roma.",
                keywords=["rooftop", "the flair", "terrazza", "ristorante", "cena panoramica"],
            ),
            FAQItem(
                id="faq_allergies",
                category="allergie",
                question_it="Avete piatti senza glutine o per allergie?",
                answer_it="Proponiamo alternative certificate senza glutine e per vegetariani sia per la colazione che al ristorante. Raccomandiamo sempre di segnalare eventuali allergie specifiche all'arrivo per consentire allo chef di procedere con la massima sicurezza.",
                keywords=[
                    "celiachia",
                    "senza glutine",
                    "glutine",
                    "allergia",
                    "allergie",
                    "vegetariano",
                    "vegano",
                ],
            ),
            FAQItem(
                id="faq_location",
                category="indirizzo",
                question_it="Dove vi trovate?",
                answer_it="Sina Bernini Bristol si trova in Piazza Barberini 23, 00187 Roma, proprio di fronte alla Fontana del Tritone e all'inizio di Via Veneto.",
                keywords=["dove siete", "indirizzo", "posizione", "come arrivare", "piazza barberini"],
            ),
        ],
    )


def get_default_seed_tables(restaurant_id: str = "default_trattoria") -> list[Table]:
    return [
        Table(
            id="T1",
            restaurant_id=restaurant_id,
            table_number=1,
            min_capacity=1,
            max_capacity=2,
        ),
        Table(
            id="T2",
            restaurant_id=restaurant_id,
            table_number=2,
            min_capacity=1,
            max_capacity=2,
        ),
        Table(
            id="T3",
            restaurant_id=restaurant_id,
            table_number=3,
            min_capacity=3,
            max_capacity=4,
        ),
        Table(
            id="T4",
            restaurant_id=restaurant_id,
            table_number=4,
            min_capacity=3,
            max_capacity=4,
        ),
        Table(
            id="T5",
            restaurant_id=restaurant_id,
            table_number=5,
            min_capacity=5,
            max_capacity=6,
        ),
        Table(
            id="T6",
            restaurant_id=restaurant_id,
            table_number=6,
            min_capacity=7,
            max_capacity=10,
        ),
    ]


class InMemoryRestaurantRepository(BaseRestaurantRepository):
    def __init__(self, restaurant_id: str = "default_trattoria"):
        self.restaurant = get_default_seed_restaurant(restaurant_id)
        self.tables = get_default_seed_tables(restaurant_id)

    async def get_settings(self, restaurant_id: str) -> RestaurantSettings | None:
        if restaurant_id == self.restaurant.id:
            return self.restaurant
        return None

    async def get_tables(self, restaurant_id: str) -> list[Table]:
        return [
            t for t in self.tables if t.restaurant_id == restaurant_id and t.is_active
        ]

    async def get_faqs(self, restaurant_id: str) -> list[FAQItem]:
        if restaurant_id == self.restaurant.id:
            return self.restaurant.faqs
        return []


class InMemoryBookingRepository(BaseBookingRepository):
    def __init__(self):
        self._reservations: dict[str, Reservation] = {}

    async def get_reservations_for_date(
        self,
        restaurant_id: str,
        booking_date: date,
        status: BookingStatus | None = BookingStatus.CONFIRMED,
    ) -> list[Reservation]:
        results = []
        for r in self._reservations.values():
            if (
                r.restaurant_id == restaurant_id
                and r.booking_date == booking_date
                and (status is None or r.status == status)
            ):
                results.append(r)
        return results

    async def get_by_reference(self, reference_code: str) -> Reservation | None:
        code = reference_code.strip().upper()
        for r in self._reservations.values():
            if r.reference_code.upper() == code:
                return r
        return None

    async def get_by_customer_phone(self, phone: str) -> list[Reservation]:
        clean_phone = phone.replace(" ", "").replace("-", "")
        results = []
        for r in self._reservations.values():
            if r.customer_phone.replace(" ", "").replace("-", "") == clean_phone:
                results.append(r)
        return results

    async def create_reservation(self, reservation: Reservation) -> Reservation:
        self._reservations[reservation.id] = reservation
        return reservation

    async def update_reservation(self, reservation: Reservation) -> Reservation:
        self._reservations[reservation.id] = reservation
        return reservation


class InMemoryNotificationRepository(BaseNotificationRepository):
    def __init__(self):
        self._notifications: list[CRMNotification] = []

    async def add_notification(self, notification: CRMNotification) -> CRMNotification:
        self._notifications.insert(0, notification)
        return notification

    async def get_notifications(
        self, restaurant_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[CRMNotification]:
        res = [
            n
            for n in self._notifications
            if n.restaurant_id == restaurant_id and (not unread_only or not n.is_read)
        ]
        return res[:limit]

    async def mark_as_read(self, notification_id: str) -> bool:
        for n in self._notifications:
            if n.id == notification_id:
                n.is_read = True
                return True
        return False


def normalize_phone_number(phone: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    # If phone starts with 0039, replace with +39
    if cleaned.startswith("0039"):
        cleaned = "+39" + cleaned[4:]
    return cleaned


class InMemoryGuestCRMRepository(BaseGuestCRMRepository):
    def __init__(self):
        # Seed with sample data
        self._properties: dict[str, HotelProperty] = {
            p_id: prop.model_copy(deep=True)
            for p_id, prop in SAMPLE_PROPERTIES.items()
        }
        self._guests: dict[str, GuestProfile] = {
            guest.id: guest.model_copy(deep=True) for guest in SAMPLE_GUESTS.values()
        }
        self._stays: dict[str, HotelStay] = {
            stay.id: stay.model_copy(deep=True) for stay in SAMPLE_STAYS.values()
        }
        self._recommendations: list[CityRecommendationItem] = [
            r.model_copy(deep=True) for r in SAMPLE_RECOMMENDATIONS
        ]
        self._concierge_requests: list[ConciergeRequest] = []
        self._feedback_list: list[GuestFeedback] = []

    async def get_guest_by_phone(self, phone: str) -> GuestProfile | None:
        target = normalize_phone_number(phone)
        for guest in self._guests.values():
            if normalize_phone_number(guest.phone_number) == target:
                return guest.model_copy(deep=True)
        return None

    async def get_guest_by_id(self, guest_id: str) -> GuestProfile | None:
        guest = self._guests.get(guest_id)
        return guest.model_copy(deep=True) if guest else None

    async def save_guest(self, guest: GuestProfile) -> GuestProfile:
        self._guests[guest.id] = guest.model_copy(deep=True)
        return guest

    async def get_active_or_upcoming_stay(self, guest_id: str) -> HotelStay | None:
        # Match stay for this guest
        for stay in self._stays.values():
            if stay.guest_id == guest_id:
                return stay.model_copy(deep=True)
        return None

    async def get_stay_by_id(self, stay_id: str) -> HotelStay | None:
        stay = self._stays.get(stay_id)
        return stay.model_copy(deep=True) if stay else None

    async def save_stay(self, stay: HotelStay) -> HotelStay:
        self._stays[stay.id] = stay.model_copy(deep=True)
        return stay

    async def get_hotel_property(self, hotel_id: str) -> HotelProperty | None:
        prop = self._properties.get(hotel_id)
        return prop.model_copy(deep=True) if prop else None

    async def add_concierge_request(
        self, request: ConciergeRequest
    ) -> ConciergeRequest:
        self._concierge_requests.insert(0, request.model_copy(deep=True))
        return request

    async def get_concierge_requests(
        self, stay_id: str | None = None, guest_id: str | None = None
    ) -> list[ConciergeRequest]:
        results = self._concierge_requests
        if stay_id:
            results = [r for r in results if r.stay_id == stay_id]
        if guest_id:
            results = [r for r in results if r.guest_id == guest_id]
        return [r.model_copy(deep=True) for r in results]

    async def get_city_recommendations(
        self,
        hotel_id: str,
        persona: TravelPersona | None = None,
        category: ConciergeCategory | None = None,
    ) -> list[CityRecommendationItem]:
        items = [r for r in self._recommendations if r.hotel_id == hotel_id]
        if category:
            items = [r for r in items if r.category == category]
        if persona:
            # Sort or filter items matching persona first
            matching = [r for r in items if persona in r.recommended_for]
            others = [r for r in items if persona not in r.recommended_for]
            return [r.model_copy(deep=True) for r in matching + others]
        return [r.model_copy(deep=True) for r in items]

    async def record_feedback(self, feedback: GuestFeedback) -> GuestFeedback:
        self._feedback_list.append(feedback.model_copy(deep=True))
        return feedback

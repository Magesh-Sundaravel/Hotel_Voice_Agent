from datetime import date

from src.models import (
    BookingStatus,
    CRMNotification,
    FAQItem,
    Reservation,
    RestaurantSettings,
    Shift,
    ShiftName,
    Table,
)
from src.repositories.base import (
    BaseBookingRepository,
    BaseNotificationRepository,
    BaseRestaurantRepository,
)


def get_default_seed_restaurant(
    restaurant_id: str = "default_trattoria",
) -> RestaurantSettings:
    return RestaurantSettings(
        id=restaurant_id,
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
                answer_it="Siamo in Via Roma 42, a 5 minuti a piedi da Piazza del Popolo.",
                keywords=["dove siete", "indirizzo", "posizione", "come arrivare"],
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

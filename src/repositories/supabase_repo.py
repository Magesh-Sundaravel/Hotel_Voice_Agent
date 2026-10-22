from datetime import UTC, date, datetime

from supabase import Client, create_client

from src.config import settings
from src.models import (
    BookingStatus,
    CRMNotification,
    FAQItem,
    Reservation,
    RestaurantSettings,
    Shift,
    Table,
)
from src.repositories.base import (
    BaseBookingRepository,
    BaseNotificationRepository,
    BaseRestaurantRepository,
)


def get_supabase_client() -> Client | None:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return None


class SupabaseRestaurantRepository(BaseRestaurantRepository):
    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def get_settings(self, restaurant_id: str) -> RestaurantSettings | None:
        if not self.client:
            return None
        res = (
            self.client.table("restaurants")
            .select("*")
            .eq("id", restaurant_id)
            .execute()
        )
        if not res.data:
            return None
        row = res.data[0]
        faqs = await self.get_faqs(restaurant_id)
        shifts = [Shift(**s) for s in row.get("shifts", [])]
        return RestaurantSettings(
            id=row["id"],
            name=row["name"],
            phone_number=row["phone_number"],
            address=row.get("address", ""),
            timezone=row.get("timezone", "Europe/Rome"),
            slot_duration_minutes=row.get("slot_duration_minutes", 90),
            max_party_size=row.get("max_party_size", 10),
            shifts=shifts,
            faqs=faqs,
        )

    async def get_tables(self, restaurant_id: str) -> list[Table]:
        if not self.client:
            return []
        res = (
            self.client.table("tables")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .eq("is_active", True)
            .execute()
        )
        return [Table(**row) for row in res.data]

    async def get_faqs(self, restaurant_id: str) -> list[FAQItem]:
        if not self.client:
            return []
        res = (
            self.client.table("faqs")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .execute()
        )
        return [FAQItem(**row) for row in res.data]


class SupabaseBookingRepository(BaseBookingRepository):
    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def get_reservations_for_date(
        self,
        restaurant_id: str,
        booking_date: date,
        status: BookingStatus | None = BookingStatus.CONFIRMED,
    ) -> list[Reservation]:
        if not self.client:
            return []
        query = (
            self.client.table("reservations")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .eq("booking_date", booking_date.isoformat())
        )
        if status:
            query = query.eq("status", status.value)
        res = query.execute()
        return [Reservation(**row) for row in res.data]

    async def get_by_reference(self, reference_code: str) -> Reservation | None:
        if not self.client:
            return None
        res = (
            self.client.table("reservations")
            .select("*")
            .ilike("reference_code", reference_code.strip())
            .execute()
        )
        if not res.data:
            return None
        return Reservation(**res.data[0])

    async def get_by_customer_phone(self, phone: str) -> list[Reservation]:
        if not self.client:
            return []
        res = (
            self.client.table("reservations")
            .select("*")
            .eq("customer_phone", phone.strip())
            .execute()
        )
        return [Reservation(**row) for row in res.data]

    async def create_reservation(self, reservation: Reservation) -> Reservation:
        if not self.client:
            raise RuntimeError("Supabase client is not configured")
        data = reservation.model_dump(mode="json")
        self.client.table("reservations").insert(data).execute()
        return reservation

    async def update_reservation(self, reservation: Reservation) -> Reservation:
        if not self.client:
            raise RuntimeError("Supabase client is not configured")
        data = reservation.model_dump(mode="json")
        data["updated_at"] = datetime.now(UTC).isoformat()
        self.client.table("reservations").update(data).eq(
            "id", reservation.id
        ).execute()
        return reservation


class SupabaseNotificationRepository(BaseNotificationRepository):
    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def add_notification(self, notification: CRMNotification) -> CRMNotification:
        if not self.client:
            return notification
        data = notification.model_dump(mode="json")
        self.client.table("crm_notifications").insert(data).execute()
        return notification

    async def get_notifications(
        self, restaurant_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[CRMNotification]:
        if not self.client:
            return []
        query = (
            self.client.table("crm_notifications")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if unread_only:
            query = query.eq("is_read", False)
        res = query.execute()
        return [CRMNotification(**row) for row in res.data]

    async def mark_as_read(self, notification_id: str) -> bool:
        if not self.client:
            return False
        res = (
            self.client.table("crm_notifications")
            .update({"is_read": True})
            .eq("id", notification_id)
            .execute()
        )
        return len(res.data) > 0

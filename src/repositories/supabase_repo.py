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
from src.repositories.memory_repo import (
    InMemoryBookingRepository,
    InMemoryNotificationRepository,
    InMemoryRestaurantRepository,
)

_fallback_restaurant_repo = InMemoryRestaurantRepository()
_fallback_booking_repo = InMemoryBookingRepository()
_fallback_notification_repo = InMemoryNotificationRepository()


def get_supabase_client() -> Client | None:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return None


class SupabaseRestaurantRepository(BaseRestaurantRepository):
    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def get_settings(self, restaurant_id: str) -> RestaurantSettings | None:
        if not self.client:
            return await _fallback_restaurant_repo.get_settings(restaurant_id)
        try:
            res = (
                self.client.table("restaurants")
                .select("*")
                .eq("id", restaurant_id)
                .execute()
            )
            if not res.data:
                return await _fallback_restaurant_repo.get_settings(restaurant_id)
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
        except Exception:
            return await _fallback_restaurant_repo.get_settings(restaurant_id)

    async def get_tables(self, restaurant_id: str) -> list[Table]:
        if not self.client:
            return await _fallback_restaurant_repo.get_tables(restaurant_id)
        try:
            res = (
                self.client.table("tables")
                .select("*")
                .eq("restaurant_id", restaurant_id)
                .eq("is_active", True)
                .execute()
            )
            return [Table(**row) for row in res.data]
        except Exception:
            return await _fallback_restaurant_repo.get_tables(restaurant_id)

    async def get_faqs(self, restaurant_id: str) -> list[FAQItem]:
        if not self.client:
            return await _fallback_restaurant_repo.get_faqs(restaurant_id)
        try:
            res = (
                self.client.table("faqs")
                .select("*")
                .eq("restaurant_id", restaurant_id)
                .execute()
            )
            return [FAQItem(**row) for row in res.data]
        except Exception:
            return await _fallback_restaurant_repo.get_faqs(restaurant_id)


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
            return await _fallback_booking_repo.get_reservations_for_date(
                restaurant_id, booking_date, status
            )
        try:
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
        except Exception:
            return await _fallback_booking_repo.get_reservations_for_date(
                restaurant_id, booking_date, status
            )

    async def get_by_reference(self, reference_code: str) -> Reservation | None:
        if not self.client:
            return await _fallback_booking_repo.get_by_reference(reference_code)
        try:
            res = (
                self.client.table("reservations")
                .select("*")
                .ilike("reference_code", reference_code.strip())
                .execute()
            )
            if not res.data:
                return await _fallback_booking_repo.get_by_reference(reference_code)
            return Reservation(**res.data[0])
        except Exception:
            return await _fallback_booking_repo.get_by_reference(reference_code)

    async def get_by_customer_phone(self, phone: str) -> list[Reservation]:
        if not self.client:
            return await _fallback_booking_repo.get_by_customer_phone(phone)
        try:
            res = (
                self.client.table("reservations")
                .select("*")
                .eq("customer_phone", phone.strip())
                .execute()
            )
            return [Reservation(**row) for row in res.data]
        except Exception:
            return await _fallback_booking_repo.get_by_customer_phone(phone)

    async def create_reservation(self, reservation: Reservation) -> Reservation:
        await _fallback_booking_repo.create_reservation(reservation)
        if self.client:
            try:
                data = reservation.model_dump(mode="json")
                self.client.table("reservations").insert(data).execute()
            except Exception:
                pass
        return reservation

    async def update_reservation(self, reservation: Reservation) -> Reservation:
        await _fallback_booking_repo.update_reservation(reservation)
        if self.client:
            try:
                data = reservation.model_dump(mode="json")
                data["updated_at"] = datetime.now(UTC).isoformat()
                self.client.table("reservations").update(data).eq(
                    "id", reservation.id
                ).execute()
            except Exception:
                pass
        return reservation


class SupabaseNotificationRepository(BaseNotificationRepository):
    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    async def add_notification(self, notification: CRMNotification) -> CRMNotification:
        await _fallback_notification_repo.add_notification(notification)
        if self.client:
            try:
                data = notification.model_dump(mode="json")
                self.client.table("crm_notifications").insert(data).execute()
            except Exception:
                pass
        return notification

    async def get_notifications(
        self, restaurant_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[CRMNotification]:
        if not self.client:
            return await _fallback_notification_repo.get_notifications(
                restaurant_id, unread_only, limit
            )
        try:
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
            if not res.data:
                return await _fallback_notification_repo.get_notifications(
                    restaurant_id, unread_only, limit
                )
            return [CRMNotification(**row) for row in res.data]
        except Exception:
            return await _fallback_notification_repo.get_notifications(
                restaurant_id, unread_only, limit
            )

    async def mark_as_read(self, notification_id: str) -> bool:
        await _fallback_notification_repo.mark_as_read(notification_id)
        if self.client:
            try:
                res = (
                    self.client.table("crm_notifications")
                    .update({"is_read": True})
                    .eq("id", notification_id)
                    .execute()
                )
                return len(res.data) > 0
            except Exception:
                pass
        return True

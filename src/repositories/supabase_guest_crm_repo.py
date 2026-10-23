import logging
from datetime import UTC, datetime

from supabase import Client

from src.models.crm import (
    CityRecommendationItem,
    ConciergeCategory,
    ConciergeRequest,
    GuestFeedback,
    GuestPreferences,
    GuestProfile,
    HotelProperty,
    HotelStay,
    TravelPersona,
)
from src.repositories.base import BaseGuestCRMRepository
from src.repositories.memory_repo import (
    InMemoryGuestCRMRepository,
    normalize_phone_number,
)
from src.repositories.supabase_repo import get_supabase_client

logger = logging.getLogger(__name__)

_fallback_guest_crm_repo = InMemoryGuestCRMRepository()


class SupabaseGuestCRMRepository(BaseGuestCRMRepository):
    def __init__(
        self,
        client: Client | None = None,
        fallback_repo: BaseGuestCRMRepository | None = None,
    ):
        self.client = client or get_supabase_client()
        self._fallback = fallback_repo or _fallback_guest_crm_repo

    def _row_to_guest(self, row: dict) -> GuestProfile:
        prefs = GuestPreferences(
            dietary_restrictions=row.get("dietary_restrictions") or [],
            room_preferences=row.get("room_preferences") or [],
            favorite_drinks=row.get("favorite_drinks") or [],
            special_notes=row.get("special_notes"),
        )
        data = {**row}
        data["preferences"] = prefs
        return GuestProfile(**data)

    def _guest_to_row(self, guest: GuestProfile) -> dict:
        row = guest.model_dump(mode="json")
        prefs = row.pop("preferences", {})
        row["dietary_restrictions"] = prefs.get("dietary_restrictions", [])
        row["room_preferences"] = prefs.get("room_preferences", [])
        row["favorite_drinks"] = prefs.get("favorite_drinks", [])
        row["special_notes"] = prefs.get("special_notes")
        return row

    async def get_all_guests(self) -> list[GuestProfile]:
        if not self.client:
            return await self._fallback.get_all_guests()
        try:
            res = self.client.table("crm_guests").select("*").execute()
            if not res.data:
                return await self._fallback.get_all_guests()
            return [self._row_to_guest(row) for row in res.data]
        except Exception as e:
            logger.warning("Supabase get_all_guests failed: %s", e)
            return await self._fallback.get_all_guests()

    async def get_guest_by_phone(self, phone: str) -> GuestProfile | None:
        if not self.client:
            return await self._fallback.get_guest_by_phone(phone)
        try:
            target = normalize_phone_number(phone)
            res = (
                self.client.table("crm_guests")
                .select("*")
                .eq("phone_number", target)
                .execute()
            )
            if res.data:
                return self._row_to_guest(res.data[0])

            # Try raw phone string
            raw_target = phone.strip()
            if raw_target != target:
                res = (
                    self.client.table("crm_guests")
                    .select("*")
                    .eq("phone_number", raw_target)
                    .execute()
                )
                if res.data:
                    return self._row_to_guest(res.data[0])

            # Fallback to scanning all guests
            all_g = await self.get_all_guests()
            for g in all_g:
                if normalize_phone_number(g.phone_number) == target:
                    return g
            return None
        except Exception as e:
            logger.warning("Supabase get_guest_by_phone failed for %s: %s", phone, e)
            return await self._fallback.get_guest_by_phone(phone)

    async def get_guest_by_id(self, guest_id: str) -> GuestProfile | None:
        if not self.client:
            return await self._fallback.get_guest_by_id(guest_id)
        try:
            res = (
                self.client.table("crm_guests")
                .select("*")
                .eq("id", guest_id)
                .execute()
            )
            if not res.data:
                return await self._fallback.get_guest_by_id(guest_id)
            return self._row_to_guest(res.data[0])
        except Exception as e:
            logger.warning("Supabase get_guest_by_id failed for %s: %s", guest_id, e)
            return await self._fallback.get_guest_by_id(guest_id)

    async def save_guest(self, guest: GuestProfile) -> GuestProfile:
        await self._fallback.save_guest(guest)
        if self.client:
            try:
                row = self._guest_to_row(guest)
                row["updated_at"] = datetime.now(UTC).isoformat()
                self.client.table("crm_guests").upsert(row).execute()
            except Exception as e:
                logger.warning("Supabase save_guest failed: %s", e)
        return guest

    async def get_active_or_upcoming_stay(self, guest_id: str) -> HotelStay | None:
        if not self.client:
            return await self._fallback.get_active_or_upcoming_stay(guest_id)
        try:
            res = (
                self.client.table("hotel_stays")
                .select("*")
                .eq("guest_id", guest_id)
                .order("created_at", desc=True)
                .execute()
            )
            if not res.data:
                return await self._fallback.get_active_or_upcoming_stay(guest_id)
            return HotelStay(**res.data[0])
        except Exception as e:
            logger.warning("Supabase get_active_or_upcoming_stay failed for %s: %s", guest_id, e)
            return await self._fallback.get_active_or_upcoming_stay(guest_id)

    async def get_stay_by_id(self, stay_id: str) -> HotelStay | None:
        if not self.client:
            return await self._fallback.get_stay_by_id(stay_id)
        try:
            res = (
                self.client.table("hotel_stays")
                .select("*")
                .eq("id", stay_id)
                .execute()
            )
            if not res.data:
                return await self._fallback.get_stay_by_id(stay_id)
            return HotelStay(**res.data[0])
        except Exception as e:
            logger.warning("Supabase get_stay_by_id failed for %s: %s", stay_id, e)
            return await self._fallback.get_stay_by_id(stay_id)

    async def save_stay(self, stay: HotelStay) -> HotelStay:
        await self._fallback.save_stay(stay)
        if self.client:
            try:
                data = stay.model_dump(mode="json")
                self.client.table("hotel_stays").upsert(data).execute()
            except Exception as e:
                logger.warning("Supabase save_stay failed: %s", e)
        return stay

    async def get_hotel_property(self, hotel_id: str) -> HotelProperty | None:
        if not self.client:
            return await self._fallback.get_hotel_property(hotel_id)
        try:
            res = (
                self.client.table("hotels")
                .select("*")
                .eq("id", hotel_id)
                .execute()
            )
            if not res.data:
                return await self._fallback.get_hotel_property(hotel_id)
            row = res.data[0]
            return HotelProperty(**row)
        except Exception as e:
            logger.warning("Supabase get_hotel_property failed for %s: %s", hotel_id, e)
            return await self._fallback.get_hotel_property(hotel_id)

    async def add_concierge_request(
        self, request: ConciergeRequest
    ) -> ConciergeRequest:
        await self._fallback.add_concierge_request(request)
        if self.client:
            try:
                data = request.model_dump(mode="json")
                self.client.table("concierge_requests").insert(data).execute()
            except Exception as e:
                logger.warning("Supabase add_concierge_request failed: %s", e)
        return request

    async def get_concierge_requests(
        self, stay_id: str | None = None, guest_id: str | None = None
    ) -> list[ConciergeRequest]:
        if not self.client:
            return await self._fallback.get_concierge_requests(stay_id, guest_id)
        try:
            query = self.client.table("concierge_requests").select("*")
            if stay_id:
                query = query.eq("stay_id", stay_id)
            if guest_id:
                query = query.eq("guest_id", guest_id)
            res = query.order("created_at", desc=True).execute()
            if not res.data:
                return await self._fallback.get_concierge_requests(stay_id, guest_id)
            return [ConciergeRequest(**row) for row in res.data]
        except Exception as e:
            logger.warning("Supabase get_concierge_requests failed: %s", e)
            return await self._fallback.get_concierge_requests(stay_id, guest_id)

    async def get_city_recommendations(
        self,
        hotel_id: str,
        persona: TravelPersona | None = None,
        category: ConciergeCategory | None = None,
    ) -> list[CityRecommendationItem]:
        if not self.client:
            return await self._fallback.get_city_recommendations(hotel_id, persona, category)
        try:
            query = self.client.table("city_recommendations").select("*").eq("hotel_id", hotel_id)
            if category:
                query = query.eq("category", category.value if hasattr(category, "value") else str(category))
            res = query.execute()
            if not res.data:
                return await self._fallback.get_city_recommendations(hotel_id, persona, category)
            items = [CityRecommendationItem(**row) for row in res.data]
            if persona:
                matching = [r for r in items if persona in r.recommended_for]
                others = [r for r in items if persona not in r.recommended_for]
                return matching + others
            return items
        except Exception as e:
            logger.warning("Supabase get_city_recommendations failed: %s", e)
            return await self._fallback.get_city_recommendations(hotel_id, persona, category)

    async def record_feedback(self, feedback: GuestFeedback) -> GuestFeedback:
        await self._fallback.record_feedback(feedback)
        if self.client:
            try:
                data = feedback.model_dump(mode="json")
                self.client.table("guest_feedback").insert(data).execute()
            except Exception as e:
                logger.warning("Supabase record_feedback failed: %s", e)
        return feedback

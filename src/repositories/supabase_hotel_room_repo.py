import logging
from datetime import UTC, date, datetime

from src.models.hotel_booking import HotelRoom, RoomBooking, RoomBookingStatus
from src.repositories.base import BaseHotelRoomRepository
from src.repositories.hotel_room_repo import InMemoryHotelRoomRepository
from src.repositories.supabase_repo import get_supabase_client
from supabase import Client

logger = logging.getLogger(__name__)

_fallback_hotel_room_repo = InMemoryHotelRoomRepository()


class SupabaseHotelRoomRepository(BaseHotelRoomRepository):
    def __init__(
        self,
        client: Client | None = None,
        fallback_repo: BaseHotelRoomRepository | None = None,
    ):
        self.client = client or get_supabase_client()
        self._fallback = fallback_repo or _fallback_hotel_room_repo

    async def get_all_rooms(self) -> list[HotelRoom]:
        if not self.client:
            return await self._fallback.get_all_rooms()
        try:
            res = (
                self.client.table("hotel_rooms")
                .select("*")
                .eq("is_active", True)
                .order("room_number")
                .execute()
            )
            if not res.data:
                return await self._fallback.get_all_rooms()
            return [HotelRoom(**row) for row in res.data]
        except Exception as e:
            logger.warning("Supabase get_all_rooms failed, falling back to in-memory: %s", e)
            return await self._fallback.get_all_rooms()

    async def get_room(self, room_number: str) -> HotelRoom | None:
        if not self.client:
            return await self._fallback.get_room(room_number)
        try:
            res = (
                self.client.table("hotel_rooms")
                .select("*")
                .eq("room_number", room_number)
                .execute()
            )
            if not res.data:
                return await self._fallback.get_room(room_number)
            return HotelRoom(**res.data[0])
        except Exception as e:
            logger.warning("Supabase get_room failed for %s: %s", room_number, e)
            return await self._fallback.get_room(room_number)

    async def get_all_bookings(self) -> list[RoomBooking]:
        if not self.client:
            return await self._fallback.get_all_bookings()
        try:
            res = (
                self.client.table("room_bookings")
                .select("*")
                .order("check_in_date", desc=True)
                .execute()
            )
            if not res.data:
                return await self._fallback.get_all_bookings()
            return [RoomBooking(**row) for row in res.data]
        except Exception as e:
            logger.warning("Supabase get_all_bookings failed: %s", e)
            return await self._fallback.get_all_bookings()

    async def get_booking_by_ref(self, reference_code: str) -> RoomBooking | None:
        if not self.client:
            return await self._fallback.get_booking_by_ref(reference_code)
        try:
            code = reference_code.strip()
            res = (
                self.client.table("room_bookings")
                .select("*")
                .ilike("reference_code", code)
                .execute()
            )
            if not res.data:
                return await self._fallback.get_booking_by_ref(reference_code)
            return RoomBooking(**res.data[0])
        except Exception as e:
            logger.warning("Supabase get_booking_by_ref failed for %s: %s", reference_code, e)
            return await self._fallback.get_booking_by_ref(reference_code)

    async def get_bookings_by_phone(self, phone: str) -> list[RoomBooking]:
        if not self.client:
            return await self._fallback.get_bookings_by_phone(phone)
        try:
            target = phone.strip()
            res = self.client.table("room_bookings").select("*").eq("guest_phone", target).execute()
            if not res.data:
                # Also try normalized format
                all_b = await self.get_all_bookings()
                clean = target.replace(" ", "").replace("-", "")
                return [
                    b for b in all_b if b.guest_phone.replace(" ", "").replace("-", "") == clean
                ]
            return [RoomBooking(**row) for row in res.data]
        except Exception as e:
            logger.warning("Supabase get_bookings_by_phone failed for %s: %s", phone, e)
            return await self._fallback.get_bookings_by_phone(phone)

    async def get_active_bookings_in_range(
        self, start_date: date, end_date: date
    ) -> list[RoomBooking]:
        all_bookings = await self.get_all_bookings()
        results = []
        for b in all_bookings:
            if b.status == RoomBookingStatus.CANCELLED:
                continue

            effective_end = b.check_out_date
            if b.status in [RoomBookingStatus.EARLY_DEPARTURE, RoomBookingStatus.CHECKED_OUT]:
                effective_end = b.actual_departure_date or b.check_out_date

            if start_date < effective_end and end_date > b.check_in_date:
                results.append(b)
        return results

    async def create_booking(self, booking: RoomBooking) -> RoomBooking:
        await self._fallback.create_booking(booking)
        if self.client:
            try:
                data = booking.model_dump(mode="json")
                self.client.table("room_bookings").insert(data).execute()
            except Exception as e:
                logger.warning("Supabase create_booking insert failed: %s", e)
        return booking

    async def update_booking(self, booking: RoomBooking) -> RoomBooking:
        await self._fallback.update_booking(booking)
        if self.client:
            try:
                data = booking.model_dump(mode="json")
                data["updated_at"] = datetime.now(UTC).isoformat()
                self.client.table("room_bookings").update(data).eq("id", booking.id).execute()
            except Exception as e:
                logger.warning("Supabase update_booking failed: %s", e)
        return booking

from src.repositories.base import (
    BaseBookingRepository,
    BaseGuestCRMRepository,
    BaseNotificationRepository,
    BaseRestaurantRepository,
)
from src.repositories.hotel_room_repo import (
    BaseHotelRoomRepository,
    InMemoryHotelRoomRepository,
)
from src.repositories.memory_repo import (
    InMemoryBookingRepository,
    InMemoryGuestCRMRepository,
    InMemoryNotificationRepository,
    InMemoryRestaurantRepository,
)
from src.repositories.supabase_repo import (
    SupabaseBookingRepository,
    SupabaseNotificationRepository,
    SupabaseRestaurantRepository,
    get_supabase_client,
)

# Global singleton in-memory repository for local runtime and tests
_in_memory_restaurant_repo = InMemoryRestaurantRepository()
_in_memory_booking_repo = InMemoryBookingRepository()
_in_memory_notification_repo = InMemoryNotificationRepository()
_in_memory_guest_crm_repo = InMemoryGuestCRMRepository()
_in_memory_hotel_room_repo = InMemoryHotelRoomRepository()


def get_hotel_room_repository() -> BaseHotelRoomRepository:
    return _in_memory_hotel_room_repo


def get_restaurant_repository() -> BaseRestaurantRepository:
    client = get_supabase_client()
    if client:
        return SupabaseRestaurantRepository(client)
    return _in_memory_restaurant_repo


def get_booking_repository() -> BaseBookingRepository:
    client = get_supabase_client()
    if client:
        return SupabaseBookingRepository(client)
    return _in_memory_booking_repo


def get_notification_repository() -> BaseNotificationRepository:
    client = get_supabase_client()
    if client:
        return SupabaseNotificationRepository(client)
    return _in_memory_notification_repo


def get_guest_crm_repository() -> BaseGuestCRMRepository:
    # Uses in-memory sample CRM store
    return _in_memory_guest_crm_repo


__all__ = [
    "BaseBookingRepository",
    "BaseGuestCRMRepository",
    "BaseHotelRoomRepository",
    "BaseNotificationRepository",
    "BaseRestaurantRepository",
    "InMemoryBookingRepository",
    "InMemoryGuestCRMRepository",
    "InMemoryHotelRoomRepository",
    "InMemoryNotificationRepository",
    "InMemoryRestaurantRepository",
    "SupabaseBookingRepository",
    "SupabaseNotificationRepository",
    "SupabaseRestaurantRepository",
    "get_booking_repository",
    "get_guest_crm_repository",
    "get_hotel_room_repository",
    "get_notification_repository",
    "get_restaurant_repository",
]

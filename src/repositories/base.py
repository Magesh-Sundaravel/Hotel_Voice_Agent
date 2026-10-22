from abc import ABC, abstractmethod
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
    Table,
    TravelPersona,
)


class BaseRestaurantRepository(ABC):
    @abstractmethod
    async def get_settings(self, restaurant_id: str) -> RestaurantSettings | None:
        pass

    @abstractmethod
    async def get_tables(self, restaurant_id: str) -> list[Table]:
        pass

    @abstractmethod
    async def get_faqs(self, restaurant_id: str) -> list[FAQItem]:
        pass


class BaseBookingRepository(ABC):
    @abstractmethod
    async def get_reservations_for_date(
        self,
        restaurant_id: str,
        booking_date: date,
        status: BookingStatus | None = BookingStatus.CONFIRMED,
    ) -> list[Reservation]:
        pass

    @abstractmethod
    async def get_by_reference(self, reference_code: str) -> Reservation | None:
        pass

    @abstractmethod
    async def get_by_customer_phone(self, phone: str) -> list[Reservation]:
        pass

    @abstractmethod
    async def create_reservation(self, reservation: Reservation) -> Reservation:
        pass

    @abstractmethod
    async def update_reservation(self, reservation: Reservation) -> Reservation:
        pass


class BaseNotificationRepository(ABC):
    @abstractmethod
    async def add_notification(self, notification: CRMNotification) -> CRMNotification:
        pass

    @abstractmethod
    async def get_notifications(
        self, restaurant_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[CRMNotification]:
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: str) -> bool:
        pass


class BaseGuestCRMRepository(ABC):
    @abstractmethod
    async def get_guest_by_phone(self, phone: str) -> GuestProfile | None:
        pass

    @abstractmethod
    async def get_guest_by_id(self, guest_id: str) -> GuestProfile | None:
        pass

    @abstractmethod
    async def save_guest(self, guest: GuestProfile) -> GuestProfile:
        pass

    @abstractmethod
    async def get_active_or_upcoming_stay(self, guest_id: str) -> HotelStay | None:
        pass

    @abstractmethod
    async def get_stay_by_id(self, stay_id: str) -> HotelStay | None:
        pass

    @abstractmethod
    async def save_stay(self, stay: HotelStay) -> HotelStay:
        pass

    @abstractmethod
    async def get_hotel_property(self, hotel_id: str) -> HotelProperty | None:
        pass

    @abstractmethod
    async def add_concierge_request(
        self, request: ConciergeRequest
    ) -> ConciergeRequest:
        pass

    @abstractmethod
    async def get_concierge_requests(
        self, stay_id: str | None = None, guest_id: str | None = None
    ) -> list[ConciergeRequest]:
        pass

    @abstractmethod
    async def get_city_recommendations(
        self,
        hotel_id: str,
        persona: TravelPersona | None = None,
        category: ConciergeCategory | None = None,
    ) -> list[CityRecommendationItem]:
        pass

    @abstractmethod
    async def record_feedback(self, feedback: GuestFeedback) -> GuestFeedback:
        pass

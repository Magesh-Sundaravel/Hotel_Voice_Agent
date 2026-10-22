from abc import ABC, abstractmethod
from datetime import date

from src.models import (
    BookingStatus,
    CRMNotification,
    FAQItem,
    Reservation,
    RestaurantSettings,
    Table,
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

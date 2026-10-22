import pytest

from src.repositories.memory_repo import (
    InMemoryBookingRepository,
    InMemoryNotificationRepository,
    InMemoryRestaurantRepository,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService


@pytest.fixture
def restaurant_repo():
    return InMemoryRestaurantRepository(restaurant_id="default_trattoria")


@pytest.fixture
def booking_repo():
    return InMemoryBookingRepository()


@pytest.fixture
def notification_repo():
    return InMemoryNotificationRepository()


@pytest.fixture
def availability_service(restaurant_repo, booking_repo):
    return AvailabilityService(
        restaurant_repo=restaurant_repo,
        booking_repo=booking_repo,
    )


@pytest.fixture
def notification_service(notification_repo):
    return NotificationService(notification_repo=notification_repo)


@pytest.fixture
def restaurant_service(restaurant_repo):
    return RestaurantService(restaurant_repo=restaurant_repo)


@pytest.fixture
def booking_service(booking_repo, availability_service, notification_service):
    return BookingService(
        booking_repo=booking_repo,
        availability_service=availability_service,
        notification_service=notification_service,
    )

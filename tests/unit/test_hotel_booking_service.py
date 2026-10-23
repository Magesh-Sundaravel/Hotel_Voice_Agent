from datetime import date, timedelta
import pytest

from src.models.hotel_booking import (
    CreateRoomBookingRequest,
    MarkEarlyDepartureRequest,
    ModifyRoomBookingRequest,
    RoomBookingStatus,
    RoomCategory,
)
from src.repositories.hotel_room_repo import InMemoryHotelRoomRepository
from src.repositories.memory_repo import (
    InMemoryGuestCRMRepository,
    InMemoryNotificationRepository,
)
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService


@pytest.fixture
def hotel_booking_service():
    room_repo = InMemoryHotelRoomRepository()
    notif_repo = InMemoryNotificationRepository()
    crm_repo = InMemoryGuestCRMRepository()
    crm_svc = GuestCRMService(crm_repo, notif_repo)
    return HotelBookingService(
        room_repo=room_repo,
        notification_repo=notif_repo,
        guest_crm_service=crm_svc,
        hotel_id="sina_bernini_bristol",
    )


@pytest.mark.asyncio
async def test_check_availability_future_dates(hotel_booking_service):
    d_in = date.today() + timedelta(days=10)
    d_out = date.today() + timedelta(days=13)
    res = await hotel_booking_service.check_availability(
        check_in_date=d_in,
        check_out_date=d_out,
        guests_count=2,
    )
    assert res.is_available is True
    assert res.nights == 3
    assert len(res.options) >= 2
    # Verify Deluxe is €350/night -> total €1050
    deluxe_opt = next(o for o in res.options if o.category == RoomCategory.DELUXE)
    assert deluxe_opt.price_per_night == 350.0
    assert deluxe_opt.total_price == 1050.0


@pytest.mark.asyncio
async def test_check_availability_past_date_rejected(hotel_booking_service):
    d_in = date.today() - timedelta(days=2)
    d_out = date.today() + timedelta(days=1)
    res = await hotel_booking_service.check_availability(d_in, d_out)
    assert res.is_available is False
    assert "passata" in res.message_it.lower()


@pytest.mark.asyncio
async def test_create_hotel_booking_success(hotel_booking_service):
    d_in = date.today() + timedelta(days=15)
    d_out = date.today() + timedelta(days=18)
    req = CreateRoomBookingRequest(
        guest_name="Gianni Morandi",
        guest_phone="+39 333 9999000",
        category=RoomCategory.SUPERIOR,
        check_in_date=d_in,
        check_out_date=d_out,
        guests_count=2,
        special_requests="Cuscini anallergici e piano alto",
    )
    res = await hotel_booking_service.create_booking(req)
    assert res.success is True
    assert res.booking is not None
    assert res.booking.reference_code.startswith("SINA-")
    assert res.booking.room_number in ["101", "102"]
    assert res.booking.total_price == 750.0  # 3 nights * €250


@pytest.mark.asyncio
async def test_early_departure_marks_room_freed_and_adjusts_price(hotel_booking_service):
    # Test early departure on Roberto Ferri (reference SINA-1018, Room 101)
    req = MarkEarlyDepartureRequest(
        reference_code="SINA-1018",
        guest_phone="+39 347 1234567",
        actual_departure_date=date.today(),
        reason="Urgente impegno lavorativo a Milano",
    )
    res = await hotel_booking_service.mark_early_departure(req)
    assert res.success is True
    assert res.booking.status == RoomBookingStatus.EARLY_DEPARTURE
    assert res.booking.is_early_departure is True
    assert res.booking.actual_departure_date == date.today()


@pytest.mark.asyncio
async def test_cancel_booking_success(hotel_booking_service):
    # Book a room first
    d_in = date.today() + timedelta(days=20)
    d_out = date.today() + timedelta(days=22)
    create_res = await hotel_booking_service.create_booking(
        CreateRoomBookingRequest(
            guest_name="Fabio Rossi",
            guest_phone="+39 331 4455667",
            category=RoomCategory.DELUXE,
            check_in_date=d_in,
            check_out_date=d_out,
            guests_count=2,
        )
    )
    ref = create_res.booking.reference_code

    cancel_res = await hotel_booking_service.cancel_booking(
        reference_code=ref,
        guest_phone="+39 331 4455667",
        reason="Cambiamento data viaggio",
    )
    assert cancel_res.success is True
    assert cancel_res.booking.status == RoomBookingStatus.CANCELLED


@pytest.mark.asyncio
async def test_create_booking_reference_code_collision_resolution(hotel_booking_service, monkeypatch):
    real_get_by_ref = hotel_booking_service.room_repo.get_booking_by_ref
    first_call = True

    async def mock_get_by_ref(ref_code: str):
        nonlocal first_call
        if first_call:
            first_call = False
            # Simulate existing booking collision on the first generated code
            return object()
        return await real_get_by_ref(ref_code)

    monkeypatch.setattr(hotel_booking_service.room_repo, "get_booking_by_ref", mock_get_by_ref)

    d_in = date.today() + timedelta(days=25)
    d_out = date.today() + timedelta(days=27)
    create_res = await hotel_booking_service.create_booking(
        CreateRoomBookingRequest(
            guest_name="Marco Mengoni",
            guest_phone="+39 339 1234567",
            category=RoomCategory.SUPERIOR,
            check_in_date=d_in,
            check_out_date=d_out,
            guests_count=1,
        )
    )
    assert create_res.success is True
    assert create_res.booking.reference_code.startswith("SINA-")
    assert first_call is False  # Verify collision retry was triggered

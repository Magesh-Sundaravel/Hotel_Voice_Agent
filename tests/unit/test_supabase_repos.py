from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from src.models.crm import (
    GuestPreferences,
    GuestProfile,
)
from src.models.hotel_booking import RoomBooking, RoomBookingStatus, RoomCategory
from src.repositories.hotel_room_repo import InMemoryHotelRoomRepository
from src.repositories.memory_repo import InMemoryGuestCRMRepository
from src.repositories.supabase_guest_crm_repo import SupabaseGuestCRMRepository
from src.repositories.supabase_hotel_room_repo import SupabaseHotelRoomRepository
from src.repositories.supabase_repo import get_supabase_client


class MockTableQuery:
    def __init__(self, data):
        self._data = data

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def ilike(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def upsert(self, *args, **kwargs):
        return self

    def execute(self):
        res = MagicMock()
        res.data = self._data
        return res


class MockSupabaseClient:
    def __init__(self, tables_data=None):
        self.tables_data = tables_data or {}
        self.last_inserted = {}

    def table(self, name: str):
        data = self.tables_data.get(name, [])
        query = MockTableQuery(data)

        # Track operations
        orig_insert = query.insert

        def track_insert(item):
            self.last_inserted[name] = item
            return orig_insert(item)

        query.insert = track_insert
        query.upsert = track_insert
        return query


@pytest.mark.asyncio
async def test_supabase_hotel_room_repo_mock():
    mock_rooms = [
        {
            "room_number": "101",
            "category": "superior",
            "name": "Camera Superior 101",
            "price_per_night": 250.0,
            "max_guests": 2,
            "floor": 1,
            "features": ["Letto King"],
            "is_clean": True,
            "is_active": True,
        }
    ]
    mock_bookings = [
        {
            "id": "book_test_1",
            "reference_code": "SINA-9999",
            "hotel_id": "sina_bernini_bristol",
            "guest_name": "Test Guest",
            "guest_phone": "+393339999999",
            "guest_email": "test@example.com",
            "room_number": "101",
            "room_category": "superior",
            "check_in_date": "2026-11-01",
            "check_out_date": "2026-11-03",
            "nights": 2,
            "guests_count": 2,
            "price_per_night": 250.0,
            "total_price": 500.0,
            "status": "confirmed",
        }
    ]
    client = MockSupabaseClient(
        {
            "hotel_rooms": mock_rooms,
            "room_bookings": mock_bookings,
        }
    )

    fallback = InMemoryHotelRoomRepository()
    repo = SupabaseHotelRoomRepository(client=client, fallback_repo=fallback)

    # get_all_rooms
    rooms = await repo.get_all_rooms()
    assert len(rooms) == 1
    assert rooms[0].room_number == "101"

    # get_room
    room = await repo.get_room("101")
    assert room is not None
    assert room.name == "Camera Superior 101"

    # get_all_bookings
    bookings = await repo.get_all_bookings()
    assert len(bookings) == 1
    assert bookings[0].reference_code == "SINA-9999"

    # get_booking_by_ref
    b_ref = await repo.get_booking_by_ref("SINA-9999")
    assert b_ref is not None
    assert b_ref.guest_name == "Test Guest"

    # create_booking
    new_b = RoomBooking(
        id="book_new_123",
        reference_code="SINA-1234",
        guest_name="Nuovo Ospite",
        guest_phone="+393330001111",
        room_number="101",
        room_category=RoomCategory.SUPERIOR,
        check_in_date=date(2026, 11, 5),
        check_out_date=date(2026, 11, 7),
        nights=2,
        guests_count=2,
        price_per_night=250.0,
        total_price=500.0,
    )
    saved = await repo.create_booking(new_b)
    assert saved.id == "book_new_123"
    assert client.last_inserted.get("room_bookings") is not None
    assert client.last_inserted["room_bookings"]["reference_code"] == "SINA-1234"


@pytest.mark.asyncio
async def test_supabase_guest_crm_repo_mock():
    mock_guests = [
        {
            "id": "guest_mock_1",
            "phone_number": "+393331112233",
            "first_name": "Mario",
            "last_name": "Rossi",
            "preferred_language": "it",
            "vip_tier": "gold",
            "persona": "romantic_couple",
            "dietary_restrictions": ["senza glutine"],
            "room_preferences": ["piano alto"],
            "favorite_drinks": ["Franciacorta"],
            "special_notes": "Anniversario",
            "total_stays": 2,
            "loyalty_points": 1000,
        }
    ]
    client = MockSupabaseClient({"crm_guests": mock_guests})
    fallback = InMemoryGuestCRMRepository()
    repo = SupabaseGuestCRMRepository(client=client, fallback_repo=fallback)

    # get_all_guests
    guests = await repo.get_all_guests()
    assert len(guests) == 1
    assert guests[0].last_name == "Rossi"
    assert "senza glutine" in guests[0].preferences.dietary_restrictions

    # get_guest_by_phone
    g = await repo.get_guest_by_phone("+393331112233")
    assert g is not None
    assert g.first_name == "Mario"

    # save_guest
    new_g = GuestProfile(
        id="guest_new_99",
        phone_number="+393409876543",
        first_name="Giulia",
        last_name="Verdi",
        preferences=GuestPreferences(
            dietary_restrictions=["vegetariana"],
            favorite_drinks=["Prosecco"],
        ),
    )
    saved = await repo.save_guest(new_g)
    assert saved.id == "guest_new_99"
    assert client.last_inserted.get("crm_guests") is not None
    assert client.last_inserted["crm_guests"]["first_name"] == "Giulia"
    assert "vegetariana" in client.last_inserted["crm_guests"]["dietary_restrictions"]


@pytest.mark.asyncio
async def test_supabase_repos_fallback_on_error():
    class FailingClient:
        def table(self, name):
            raise RuntimeError("Database unavailable")

    fallback_rooms = InMemoryHotelRoomRepository()
    fallback_crm = InMemoryGuestCRMRepository()

    room_repo = SupabaseHotelRoomRepository(client=FailingClient(), fallback_repo=fallback_rooms)
    crm_repo = SupabaseGuestCRMRepository(client=FailingClient(), fallback_repo=fallback_crm)

    # Fallback for rooms
    rooms = await room_repo.get_all_rooms()
    assert len(rooms) >= 9

    # Fallback for CRM
    guest = await crm_repo.get_guest_by_phone("+393331112233")
    assert guest is not None
    assert guest.last_name == "Rossi"


@pytest.mark.asyncio
async def test_supabase_live_integration():
    client = get_supabase_client()
    if not client:
        pytest.skip("Supabase client not configured in environment")

    room_repo = SupabaseHotelRoomRepository(client=client)
    crm_repo = SupabaseGuestCRMRepository(client=client)

    # 1. Verify rooms read from Supabase
    rooms = await room_repo.get_all_rooms()
    assert len(rooms) >= 9
    assert any(r.room_number == "101" for r in rooms)

    # 2. Verify guest read from Supabase
    guest = await crm_repo.get_guest_by_phone("+393331112233")
    assert guest is not None
    assert guest.last_name == "Rossi"

    # 3. Create a unique booking in Supabase and read it back
    test_ref = f"SINA-TEST-{date.today().strftime('%m%d')}"
    booking = RoomBooking(
        id=f"test_booking_{test_ref}",
        reference_code=test_ref,
        guest_name="Integrazione Supabase",
        guest_phone="+393330009988",
        room_number="102",
        room_category=RoomCategory.SUPERIOR,
        check_in_date=date.today() + timedelta(days=20),
        check_out_date=date.today() + timedelta(days=22),
        nights=2,
        guests_count=2,
        price_per_night=250.0,
        total_price=500.0,
        status=RoomBookingStatus.CONFIRMED,
    )

    created = await room_repo.create_booking(booking)
    assert created.reference_code == test_ref

    # Read back by reference code
    fetched = await room_repo.get_booking_by_ref(test_ref)
    assert fetched is not None
    assert fetched.reference_code == test_ref
    assert fetched.guest_name == "Integrazione Supabase"

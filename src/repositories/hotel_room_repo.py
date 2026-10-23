from datetime import date, timedelta

from src.models.hotel_booking import (
    HotelRoom,
    RoomBooking,
    RoomBookingStatus,
    RoomCategory,
)
from src.repositories.base import BaseHotelRoomRepository

# Reference dates for sample seeding
TODAY = date.today()


# ---------------------------------------------------------------------------
# SAMPLE ROOMS SEED FOR SINA BERNINI BRISTOL
# ---------------------------------------------------------------------------
INITIAL_ROOMS = [
    HotelRoom(
        room_number="101",
        category=RoomCategory.SUPERIOR,
        name="Superior Room 101",
        price_per_night=250.0,
        max_guests=2,
        floor=1,
        features=["Letto King", "Bagno in marmo", "Affaccio cortile interno silenzioso"],
    ),
    HotelRoom(
        room_number="102",
        category=RoomCategory.SUPERIOR,
        name="Superior Room 102",
        price_per_night=250.0,
        max_guests=2,
        floor=1,
        features=["Letto Queen", "Bagno in marmo", "Doccia a pioggia"],
    ),
    HotelRoom(
        room_number="201",
        category=RoomCategory.DELUXE,
        name="Deluxe Room 201 (Piazza View)",
        price_per_night=350.0,
        max_guests=2,
        floor=2,
        features=["Vista Piazza Barberini", "Salottino", "Vasca da bagno"],
    ),
    HotelRoom(
        room_number="202",
        category=RoomCategory.DELUXE,
        name="Deluxe Room 202 (Piazza View)",
        price_per_night=350.0,
        max_guests=2,
        floor=2,
        features=["Vista Fontana del Tritone", "Letto King", "Macchina caffè Illy"],
    ),
    HotelRoom(
        room_number="203",
        category=RoomCategory.DELUXE,
        name="Deluxe Room 203",
        price_per_night=350.0,
        max_guests=2,
        floor=2,
        features=["Letto King", "Zona lavoro ergonomica", "Cabina armadio"],
    ),
    HotelRoom(
        room_number="301",
        category=RoomCategory.JUNIOR_SUITE,
        name="Junior Suite 301 con Balcone",
        price_per_night=480.0,
        max_guests=3,
        floor=3,
        features=["Balcone privato panoramico", "Divano letto", "Doccia cromoterapica"],
    ),
    HotelRoom(
        room_number="302",
        category=RoomCategory.JUNIOR_SUITE,
        name="Junior Suite 302 con Balcone",
        price_per_night=480.0,
        max_guests=3,
        floor=3,
        features=["Balcone su Via Veneto", "Salotto separato", "Vasca idromassaggio"],
    ),
    HotelRoom(
        room_number="401",
        category=RoomCategory.PANORAMIC_SUITE,
        name="Suite Panoramica 401",
        price_per_night=750.0,
        max_guests=4,
        floor=4,
        features=["Attico privato", "Terrazza 40mq", "Vista 360° su Roma", "Maggiordomo"],
    ),
    HotelRoom(
        room_number="402",
        category=RoomCategory.PANORAMIC_SUITE,
        name="Suite Panoramica Barberini 402",
        price_per_night=750.0,
        max_guests=4,
        floor=4,
        features=["Suite attico lusso", "Jacuzzi panoramica", "Bottiglia Franciacorta omaggio"],
    ),
]

# ---------------------------------------------------------------------------
# SAMPLE INITIAL BOOKINGS (In-House, Pre-Stay, Early Departure, Checked-Out)
# ---------------------------------------------------------------------------
INITIAL_BOOKINGS = [
    # 1. Marco Rossi - IN-HOUSE in Room 402 (10th Anniversary)
    RoomBooking(
        id="book_rossi_402",
        reference_code="SINA-4020",
        guest_name="Marco Rossi",
        guest_phone="+39 333 1112233",
        guest_email="marco.rossi@example.com",
        room_number="402",
        room_category=RoomCategory.PANORAMIC_SUITE,
        check_in_date=TODAY - timedelta(days=1),
        check_out_date=TODAY + timedelta(days=2),
        nights=3,
        guests_count=2,
        price_per_night=750.0,
        total_price=2250.0,
        special_requests="10° Anniversario di Nozze. Giulia è celiaca. Tavolo riservato The Flair.",
        status=RoomBookingStatus.CHECKED_IN,
    ),
    # 2. Andrea Moretti - PRE-STAY in Room 201 (Arriving Tomorrow)
    RoomBooking(
        id="book_moretti_201",
        reference_code="SINA-2015",
        guest_name="Andrea Moretti",
        guest_phone="+39 335 9988776",
        guest_email="andrea.moretti@corporate.it",
        room_number="201",
        room_category=RoomCategory.DELUXE,
        check_in_date=TODAY + timedelta(days=1),
        check_out_date=TODAY + timedelta(days=3),
        nights=2,
        guests_count=1,
        price_per_night=350.0,
        total_price=700.0,
        special_requests="Membro Sina Privilege VIP. Arrivo previsto ore 14:00 con transfer NCC.",
        is_early_check_in=True,
        status=RoomBookingStatus.CONFIRMED,
    ),
    # 3. Roberto Ferri - EARLY DEPARTURE in Room 101 (Departed early today)
    RoomBooking(
        id="book_ferri_101",
        reference_code="SINA-1018",
        guest_name="Roberto Ferri",
        guest_phone="+39 347 1234567",
        guest_email="r.ferri@business.it",
        room_number="101",
        room_category=RoomCategory.SUPERIOR,
        check_in_date=TODAY - timedelta(days=2),
        check_out_date=TODAY + timedelta(days=2),
        nights=4,
        guests_count=1,
        price_per_night=250.0,
        total_price=500.0,  # Recalculated for 2 nights
        special_requests="Camera silenziosa",
        is_early_departure=True,
        actual_departure_date=TODAY,
        early_departure_reason="Rientro anticipato urgente per impegni aziendali a Milano",
        status=RoomBookingStatus.EARLY_DEPARTURE,
    ),
    # 4. Elena Bianchi - CHECKED-OUT Room 301 (Left yesterday)
    RoomBooking(
        id="book_bianchi_301",
        reference_code="SINA-3012",
        guest_name="Elena Bianchi",
        guest_phone="+39 340 5544332",
        guest_email="elena.bianchi@gmail.com",
        room_number="301",
        room_category=RoomCategory.JUNIOR_SUITE,
        check_in_date=TODAY - timedelta(days=4),
        check_out_date=TODAY - timedelta(days=1),
        nights=3,
        guests_count=4,
        price_per_night=480.0,
        total_price=1440.0,
        special_requests="Famiglia con due bambini. Letto supplementare richiesto.",
        status=RoomBookingStatus.CHECKED_OUT,
    ),
]


class InMemoryHotelRoomRepository(BaseHotelRoomRepository):
    def __init__(self):
        self._rooms: dict[str, HotelRoom] = {
            r.room_number: r.model_copy(deep=True) for r in INITIAL_ROOMS
        }
        self._bookings: dict[str, RoomBooking] = {
            b.id: b.model_copy(deep=True) for b in INITIAL_BOOKINGS
        }

    async def get_all_rooms(self) -> list[HotelRoom]:
        return [r.model_copy(deep=True) for r in self._rooms.values()]

    async def get_room(self, room_number: str) -> HotelRoom | None:
        r = self._rooms.get(room_number)
        return r.model_copy(deep=True) if r else None

    async def get_all_bookings(self) -> list[RoomBooking]:
        # Return sorted by check-in descending
        sorted_bookings = sorted(
            self._bookings.values(), key=lambda b: b.check_in_date, reverse=True
        )
        return [b.model_copy(deep=True) for b in sorted_bookings]

    async def get_booking_by_ref(self, reference_code: str) -> RoomBooking | None:
        target = reference_code.strip().upper()
        for b in self._bookings.values():
            if b.reference_code.upper() == target:
                return b.model_copy(deep=True)
        return None

    async def get_bookings_by_phone(self, phone: str) -> list[RoomBooking]:
        clean_target = phone.replace(" ", "").replace("-", "")
        results = []
        for b in self._bookings.values():
            if b.guest_phone.replace(" ", "").replace("-", "") == clean_target:
                results.append(b.model_copy(deep=True))
        return results

    async def get_active_bookings_in_range(
        self, start_date: date, end_date: date
    ) -> list[RoomBooking]:
        """Finds bookings that overlap with [start_date, end_date) and actively hold a room."""
        results = []
        for b in self._bookings.values():
            if b.status == RoomBookingStatus.CANCELLED:
                continue

            # If marked early departure and departed on or before start_date, room is free
            effective_end = b.check_out_date
            if b.status in [RoomBookingStatus.EARLY_DEPARTURE, RoomBookingStatus.CHECKED_OUT]:
                effective_end = b.actual_departure_date or b.check_out_date

            # Overlap condition: start < effective_end and end > b.check_in_date
            if start_date < effective_end and end_date > b.check_in_date:
                results.append(b.model_copy(deep=True))
        return results

    async def create_booking(self, booking: RoomBooking) -> RoomBooking:
        self._bookings[booking.id] = booking.model_copy(deep=True)
        return booking

    async def update_booking(self, booking: RoomBooking) -> RoomBooking:
        self._bookings[booking.id] = booking.model_copy(deep=True)
        return booking

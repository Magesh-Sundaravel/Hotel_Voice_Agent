from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from src.models import (
    AvailabilityResponse,
    BookingStatus,
    Reservation,
    Table,
)
from src.repositories.base import BaseBookingRepository, BaseRestaurantRepository


def parse_hh_mm(hh_mm_str: str) -> time:
    parts = hh_mm_str.strip().split(":")
    return time(int(parts[0]), int(parts[1]))


def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def minutes_to_time_str(m: int) -> str:
    h = m // 60
    mins = m % 60
    return f"{h:02d}:{mins:02d}"


class AvailabilityService:
    def __init__(
        self,
        restaurant_repo: BaseRestaurantRepository,
        booking_repo: BaseBookingRepository,
    ):
        self.restaurant_repo = restaurant_repo
        self.booking_repo = booking_repo

    async def check_availability(
        self,
        restaurant_id: str,
        booking_date: date,
        booking_time_str: str,
        party_size: int,
        exclude_reservation_id: str | None = None,
        now_dt: datetime | None = None,
    ) -> AvailabilityResponse:
        settings = await self.restaurant_repo.get_settings(restaurant_id)
        if not settings:
            return AvailabilityResponse(
                is_available=False,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                reason="Ristorante non trovato.",
            )

        # Check for past dates or past time slots on current date
        try:
            tz = ZoneInfo(settings.timezone)
        except (KeyError, ValueError):
            tz = ZoneInfo("Europe/Rome")

        current_dt = now_dt or datetime.now(tz)
        today_in_tz = current_dt.date()

        if booking_date < today_in_tz:
            date_str = booking_date.strftime("%d/%m/%Y")
            return AvailabilityResponse(
                is_available=False,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                reason=f"Non è possibile prenotare per una data passata ({date_str}).",
            )

        if party_size > settings.max_party_size:
            return AvailabilityResponse(
                is_available=False,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                reason=(
                    f"Il numero massimo di persone prenotabili online è {settings.max_party_size}. "
                    "Per tavolate più grandi La invitiamo a lasciare un messaggio per la direzione."
                ),
            )

        try:
            req_time = parse_hh_mm(booking_time_str)
        except (ValueError, IndexError):
            return AvailabilityResponse(
                is_available=False,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                reason="Formato orario non valido. Utilizzare il formato HH:MM (es. 20:00).",
            )

        req_start_min = time_to_minutes(req_time)
        is_today = booking_date == today_in_tz
        now_minutes = time_to_minutes(current_dt.time())

        if is_today and req_start_min <= now_minutes:
            return AvailabilityResponse(
                is_available=False,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                reason=f"L'orario richiesto ({booking_time_str}) per oggi è già trascorso.",
            )

        # Check if within any shift
        matching_shift = None
        for shift in settings.shifts:
            shift_start = parse_hh_mm(shift.start_time)
            last_seating = parse_hh_mm(shift.last_seating_time)
            if shift_start <= req_time <= last_seating:
                matching_shift = shift
                break

        if not matching_shift:
            shift_desc = ", ".join(
                f"{s.name_it} ({s.start_time} - {s.last_seating_time})" for s in settings.shifts
            )
            return AvailabilityResponse(
                is_available=False,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                reason=f"Siamo chiusi alle {booking_time_str}. I nostri orari di servizio sono: {shift_desc}.",
            )

        tables = await self.restaurant_repo.get_tables(restaurant_id)
        candidate_tables = [t for t in tables if t.min_capacity <= party_size <= t.max_capacity]
        # Sort candidate tables so we pick the best fit (smallest suitable table first)
        candidate_tables.sort(key=lambda t: t.max_capacity)

        if not candidate_tables:
            # Fallback to any active table with max_capacity >= party_size
            candidate_tables = [t for t in tables if t.max_capacity >= party_size]
            candidate_tables.sort(key=lambda t: t.max_capacity)

        if not candidate_tables:
            return AvailabilityResponse(
                is_available=False,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                reason=f"Non disponiamo di tavoli per {party_size} persone.",
            )

        existing_reservations = await self.booking_repo.get_reservations_for_date(
            restaurant_id, booking_date, BookingStatus.CONFIRMED
        )

        slot_duration = settings.slot_duration_minutes
        req_end_min = req_start_min + slot_duration

        # Try to find a table available at the requested time
        available_table_id = self._find_available_table(
            candidate_tables,
            existing_reservations,
            req_start_min,
            req_end_min,
            exclude_reservation_id=exclude_reservation_id,
        )

        if available_table_id:
            return AvailabilityResponse(
                is_available=True,
                requested_date=booking_date,
                requested_time=booking_time_str,
                party_size=party_size,
                matched_table_id=available_table_id,
            )

        # If not available, search for alternative times within the matching shift
        alternatives = self._find_alternatives(
            matching_shift,
            candidate_tables,
            existing_reservations,
            slot_duration,
            req_start_min,
            exclude_reservation_id=exclude_reservation_id,
            is_today=is_today,
            now_minutes=now_minutes,
        )

        return AvailabilityResponse(
            is_available=False,
            requested_date=booking_date,
            requested_time=booking_time_str,
            party_size=party_size,
            reason="Tutti i tavoli per questo numero di coperti sono occupati all'orario richiesto.",
            alternatives=alternatives,
        )

    def _find_available_table(
        self,
        candidate_tables: list[Table],
        existing_reservations: list[Reservation],
        req_start_min: int,
        req_end_min: int,
        exclude_reservation_id: str | None = None,
    ) -> str | None:
        for table in candidate_tables:
            is_table_free = True
            for res in existing_reservations:
                if exclude_reservation_id and res.id == exclude_reservation_id:
                    continue
                if res.table_id != table.id:
                    continue
                res_start_min = time_to_minutes(parse_hh_mm(res.booking_time))
                res_end_min = res_start_min + res.duration_minutes
                # Check overlap
                if max(req_start_min, res_start_min) < min(req_end_min, res_end_min):
                    is_table_free = False
                    break
            if is_table_free:
                return table.id
        return None

    def _find_alternatives(
        self,
        shift,
        candidate_tables: list[Table],
        existing_reservations: list[Reservation],
        slot_duration: int,
        req_start_min: int,
        exclude_reservation_id: str | None = None,
        is_today: bool = False,
        now_minutes: int = 0,
    ) -> list[str]:
        shift_start_min = time_to_minutes(parse_hh_mm(shift.start_time))
        shift_last_min = time_to_minutes(parse_hh_mm(shift.last_seating_time))

        alternatives = []
        # Check every 30 minutes in shift
        candidate_slots = []
        current = shift_start_min
        while current <= shift_last_min:
            if current != req_start_min and not (is_today and current <= now_minutes):
                candidate_slots.append(current)
            current += 30

        # Sort candidate slots by proximity to requested time
        candidate_slots.sort(key=lambda slot: abs(slot - req_start_min))

        for slot_min in candidate_slots:
            slot_end_min = slot_min + slot_duration
            table_id = self._find_available_table(
                candidate_tables,
                existing_reservations,
                slot_min,
                slot_end_min,
                exclude_reservation_id=exclude_reservation_id,
            )
            if table_id:
                alternatives.append(minutes_to_time_str(slot_min))
            if len(alternatives) >= 3:
                break

        # Re-sort chronological for natural display
        alternatives.sort()
        return alternatives

import random
import re
import uuid
from datetime import UTC, datetime

from src.models import (
    BookingStatus,
    CancelReservationRequest,
    CreateReservationRequest,
    ModifyReservationRequest,
    Reservation,
    ServiceResult,
)
from src.repositories.base import BaseBookingRepository
from src.services.availability_service import AvailabilityService
from src.services.notification_service import NotificationService

TupleResult = tuple[bool, Reservation | None, str | None]


def generate_reference_code(prefix: str = "BV") -> str:
    digits = random.randint(1000, 9999)
    return f"{prefix}-{digits}"


def normalize_phone(phone: str) -> str:
    return phone.replace(" ", "").replace("-", "").replace("+", "").strip()


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 8


class BookingService:
    def __init__(
        self,
        booking_repo: BaseBookingRepository,
        availability_service: AvailabilityService,
        notification_service: NotificationService,
    ):
        self.booking_repo = booking_repo
        self.availability_service = availability_service
        self.notification_service = notification_service

    async def create_booking(
        self,
        restaurant_id: str,
        request: CreateReservationRequest,
    ) -> ServiceResult:
        # Validate customer name
        if not request.customer_name or len(request.customer_name.strip()) < 2:
            return ServiceResult(
                success=False,
                message="Customer name is required.",
                message_it="È necessario specificare un nome e cognome valido per la prenotazione.",
            )

        # Validate customer phone
        if not request.customer_phone or not is_valid_phone(request.customer_phone):
            return ServiceResult(
                success=False,
                message="Invalid phone number.",
                message_it="Il recapito telefonico inserito non è valido. Si prega di fornire un numero di telefono valido (almeno 8 cifre).",
            )

        # Check availability deterministically
        avail = await self.availability_service.check_availability(
            restaurant_id=restaurant_id,
            booking_date=request.booking_date,
            booking_time_str=request.booking_time,
            party_size=request.party_size,
        )

        if not avail.is_available or not avail.matched_table_id:
            alt_msg = ""
            if avail.alternatives:
                alt_msg = (
                    f" Orari alternativi disponibili: {', '.join(avail.alternatives)}."
                )
            reason = avail.reason or "Orario non disponibile."
            return ServiceResult(
                success=False,
                message=f"Table not available: {reason}",
                message_it=f"Purtroppo non è possibile prenotare: {reason}{alt_msg}",
            )

        ref_code = generate_reference_code()
        # Ensure code uniqueness
        while await self.booking_repo.get_by_reference(ref_code) is not None:
            ref_code = generate_reference_code()

        reservation = Reservation(
            id=str(uuid.uuid4()),
            reference_code=ref_code,
            restaurant_id=restaurant_id,
            customer_name=request.customer_name.strip(),
            customer_phone=request.customer_phone.strip(),
            party_size=request.party_size,
            booking_date=request.booking_date,
            booking_time=request.booking_time,
            duration_minutes=90,
            table_id=avail.matched_table_id,
            dietary_notes=request.dietary_notes.strip()
            if request.dietary_notes
            else None,
            special_requests=request.special_requests.strip()
            if request.special_requests
            else None,
            status=BookingStatus.CONFIRMED,
        )

        saved = await self.booking_repo.create_reservation(reservation)

        # Notify CRM
        await self.notification_service.notify_new_booking(
            restaurant_id=restaurant_id,
            reference_code=saved.reference_code,
            customer_name=saved.customer_name,
            customer_phone=saved.customer_phone,
            party_size=saved.party_size,
            booking_date=saved.booking_date.isoformat(),
            booking_time=saved.booking_time,
            dietary_notes=saved.dietary_notes,
        )

        date_formatted = saved.booking_date.strftime("%d/%m/%Y")
        msg_it = (
            f"Prenotazione confermata con successo a nome {saved.customer_name} per {saved.party_size} persone "
            f"il giorno {date_formatted} alle ore {saved.booking_time}. "
            f"Il Suo codice di prenotazione è {saved.reference_code}."
        )

        return ServiceResult(
            success=True,
            message="Reservation confirmed.",
            message_it=msg_it,
            reservation=saved,
        )

    async def verify_and_find_reservation(
        self,
        reference_code: str | None,
        customer_phone: str,
        customer_name: str | None = None,
    ) -> TupleResult:
        """Finds and verifies the caller's authority to modify or cancel."""
        caller_phone_clean = normalize_phone(customer_phone)

        # 1. If reference code is provided, look it up
        if reference_code:
            res = await self.booking_repo.get_by_reference(reference_code)
            if res:
                if normalize_phone(res.customer_phone) == caller_phone_clean:
                    return True, res, None
                # Caller phone doesn't match
                if customer_name and customer_name.lower() in res.customer_name.lower():
                    return True, res, None
                return (
                    False,
                    None,
                    "Il numero di telefono o il nome non corrispondono ai dati registrati per questo codice.",
                )

        # 2. Lookup by phone
        phone_matches = await self.booking_repo.get_by_customer_phone(customer_phone)
        active_matches = [
            r for r in phone_matches if r.status == BookingStatus.CONFIRMED
        ]

        if not active_matches:
            return (
                False,
                None,
                "Nessuna prenotazione attiva trovata associata a questo numero di telefono o codice.",
            )

        if len(active_matches) == 1:
            res = active_matches[0]
            if customer_name and (
                customer_name.lower() in res.customer_name.lower()
                or res.customer_name.lower() in customer_name.lower()
            ):
                return True, res, None
            return True, res, None

        # Multiple bookings found under same phone: require reference code or surname
        if customer_name:
            for r in active_matches:
                if customer_name.lower() in r.customer_name.lower():
                    return True, r, None

        return (
            False,
            None,
            "Sono presenti più prenotazioni a questo numero. Si prega di fornire il codice di prenotazione o il cognome.",
        )

    async def modify_booking(
        self,
        restaurant_id: str,
        request: ModifyReservationRequest,
    ) -> ServiceResult:
        verified, res, error_reason = await self.verify_and_find_reservation(
            reference_code=request.reference_code,
            customer_phone=request.customer_phone,
            customer_name=request.customer_name,
        )

        if not verified or not res:
            return ServiceResult(
                success=False,
                message="Verification failed.",
                message_it=error_reason
                or "Non è stato possibile verificare la prenotazione da modificare.",
            )

        if res.status != BookingStatus.CONFIRMED:
            return ServiceResult(
                success=False,
                message="Cannot modify non-confirmed reservation.",
                message_it=f"La prenotazione è già nello stato {res.status.value}.",
            )

        target_date = request.new_date or res.booking_date
        target_time = request.new_time or res.booking_time
        target_party_size = request.new_party_size or res.party_size

        # If date, time, or party size change, verify availability
        time_or_size_changed = (
            target_date != res.booking_date
            or target_time != res.booking_time
            or target_party_size != res.party_size
        )

        if time_or_size_changed:
            avail = await self.availability_service.check_availability(
                restaurant_id=restaurant_id,
                booking_date=target_date,
                booking_time_str=target_time,
                party_size=target_party_size,
                exclude_reservation_id=res.id,
            )
            if not avail.is_available:
                alt_msg = ""
                if avail.alternatives:
                    alt_msg = (
                        f" Alternative disponibili: {', '.join(avail.alternatives)}."
                    )
                return ServiceResult(
                    success=False,
                    message="New slot not available.",
                    message_it=f"Purtroppo non è possibile spostare la prenotazione: {avail.reason}{alt_msg}",
                )
            if avail.matched_table_id:
                res.table_id = avail.matched_table_id

        res.booking_date = target_date
        res.booking_time = target_time
        res.party_size = target_party_size
        if request.new_dietary_notes:
            res.dietary_notes = request.new_dietary_notes.strip()
        res.updated_at = datetime.now(UTC)

        updated = await self.booking_repo.update_reservation(res)

        # Notify CRM
        change_desc = f"Nuova data: {target_date}, ore: {target_time}, persone: {target_party_size}"
        await self.notification_service.notify_modification(
            restaurant_id=restaurant_id,
            reference_code=updated.reference_code,
            customer_name=updated.customer_name,
            customer_phone=updated.customer_phone,
            details=change_desc,
        )

        return ServiceResult(
            success=True,
            message="Reservation modified.",
            message_it=(
                f"La Sua prenotazione {updated.reference_code} è stata modificata con successo: "
                f"Ci vediamo il {updated.booking_date.strftime('%d/%m/%Y')} alle {updated.booking_time} per {updated.party_size} persone."
            ),
            reservation=updated,
        )

    async def cancel_booking(
        self,
        restaurant_id: str,
        request: CancelReservationRequest,
    ) -> ServiceResult:
        verified, res, error_reason = await self.verify_and_find_reservation(
            reference_code=request.reference_code,
            customer_phone=request.customer_phone,
            customer_name=request.customer_name,
        )

        if not verified or not res:
            return ServiceResult(
                success=False,
                message="Verification failed.",
                message_it=error_reason
                or "Non è stato possibile verificare la prenotazione da cancellare.",
            )

        if res.status == BookingStatus.CANCELLED:
            return ServiceResult(
                success=False,
                message="Already cancelled.",
                message_it="Questa prenotazione risulta già cancellata.",
            )

        res.status = BookingStatus.CANCELLED
        res.updated_at = datetime.now(UTC)
        updated = await self.booking_repo.update_reservation(res)

        # Notify CRM
        await self.notification_service.notify_cancellation(
            restaurant_id=restaurant_id,
            reference_code=updated.reference_code,
            customer_name=updated.customer_name,
            customer_phone=updated.customer_phone,
            reason=request.reason,
        )

        return ServiceResult(
            success=True,
            message="Reservation cancelled.",
            message_it=f"La prenotazione {updated.reference_code} è stata cancellata. Ci auguriamo di averLa presto nostro ospite in un'altra occasione.",
            reservation=updated,
        )

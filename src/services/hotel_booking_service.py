import random
import uuid
from datetime import UTC, date, datetime

from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.models.crm import TravelPersona
from src.models.hotel_booking import (
    ROOM_CATEGORY_DETAILS,
    AvailableCategoryOption,
    CreateRoomBookingRequest,
    MarkEarlyDepartureRequest,
    ModifyRoomBookingRequest,
    RoomAvailabilityResponse,
    RoomBooking,
    RoomBookingServiceResult,
    RoomBookingStatus,
    RoomCategory,
)
from src.models.notification import CRMNotification, NotificationType
from src.repositories.base import BaseNotificationRepository
from src.repositories.hotel_room_repo import BaseHotelRoomRepository
from src.services.guest_crm_service import GuestCRMService


def generate_reference_code(prefix: str = "SINA") -> str:
    """Generates a hotel booking reference code, e.g. 'SINA-4821'."""
    digits = random.randint(1000, 9999)
    return f"{prefix}-{digits}"


class HotelBookingService:
    def __init__(
        self,
        room_repo: BaseHotelRoomRepository,
        notification_repo: BaseNotificationRepository,
        guest_crm_service: GuestCRMService | None = None,
        twilio_service: TwilioService | None = None,
        email_service: EmailService | None = None,
        hotel_id: str = "sina_bernini_bristol",
    ):
        self.room_repo = room_repo
        self.notification_repo = notification_repo
        self.guest_crm_service = guest_crm_service
        self.twilio_service = twilio_service
        self.email_service = email_service
        self.hotel_id = hotel_id

    async def check_availability(
        self,
        check_in_date: date,
        check_out_date: date,
        guests_count: int = 2,
        category: RoomCategory | None = None,
    ) -> RoomAvailabilityResponse:
        # Validate dates
        today = date.today()
        if check_in_date < today:
            return RoomAvailabilityResponse(
                is_available=False,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                nights=0,
                guests_count=guests_count,
                options=[],
                message_it="La data di check-in richiesta è già passata. La prego di indicare una data odierna o futura.",
            )

        if check_out_date <= check_in_date:
            return RoomAvailabilityResponse(
                is_available=False,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                nights=0,
                guests_count=guests_count,
                options=[],
                message_it="La data di check-out deve essere successiva alla data di arrivo (minimo 1 notte).",
            )

        nights = (check_out_date - check_in_date).days

        # Get all active rooms and overlapping bookings
        all_rooms = await self.room_repo.get_all_rooms()
        active_bookings = await self.room_repo.get_active_bookings_in_range(
            check_in_date, check_out_date
        )
        occupied_room_numbers = {b.room_number for b in active_bookings}

        # Find available rooms grouped by category
        available_by_cat: dict[RoomCategory, list[str]] = {
            cat: [] for cat in RoomCategory
        }
        for room in all_rooms:
            if not room.is_active:
                continue
            if room.room_number not in occupied_room_numbers and room.max_guests >= guests_count:
                available_by_cat[room.category].append(room.room_number)

        options: list[AvailableCategoryOption] = []
        for cat, room_numbers in available_by_cat.items():
            if category and cat != category:
                continue
            if not room_numbers:
                continue

            info = ROOM_CATEGORY_DETAILS[cat]
            price_per_night = info["price_per_night"]
            options.append(
                AvailableCategoryOption(
                    category=cat,
                    name_it=info["name_it"],
                    price_per_night=price_per_night,
                    total_price=round(price_per_night * nights, 2),
                    max_guests=info["max_guests"],
                    available_rooms_count=len(room_numbers),
                    description_it=info["description_it"],
                )
            )

        is_available = len(options) > 0
        if is_available:
            cat_summaries = ", ".join(
                [f"{opt.name_it} a €{opt.price_per_night:.0f}/notte" for opt in options]
            )
            msg = (
                f"Abbiamo disponibilità per {nights} notti (dal {check_in_date.strftime('%d/%m/%Y')} "
                f"al {check_out_date.strftime('%d/%m/%Y')}) per {guests_count} ospiti. "
                f"Opzioni disponibili: {cat_summaries}."
            )
        else:
            msg = (
                f"Ci scusiamo, ma per il periodo dal {check_in_date.strftime('%d/%m/%Y')} "
                f"al {check_out_date.strftime('%d/%m/%Y')} per {guests_count} ospiti non abbiamo "
                "camere disponibili nella categoria richiesta."
            )

        return RoomAvailabilityResponse(
            is_available=is_available,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            nights=nights,
            guests_count=guests_count,
            options=options,
            message_it=msg,
        )

    async def create_booking(
        self, request: CreateRoomBookingRequest
    ) -> RoomBookingServiceResult:
        avail = await self.check_availability(
            check_in_date=request.check_in_date,
            check_out_date=request.check_out_date,
            guests_count=request.guests_count,
            category=request.category,
        )
        if not avail.is_available or not avail.options:
            return RoomBookingServiceResult(
                success=False,
                message_it="Impossibile completare la prenotazione: la camera selezionata non è disponibile per le date richieste.",
            )

        # Pick first available room in category
        all_rooms = await self.room_repo.get_all_rooms()
        active_bookings = await self.room_repo.get_active_bookings_in_range(
            request.check_in_date, request.check_out_date
        )
        occupied_numbers = {b.room_number for b in active_bookings}

        assigned_room = None
        for room in all_rooms:
            if (
                room.category == request.category
                and room.room_number not in occupied_numbers
                and room.max_guests >= request.guests_count
            ):
                assigned_room = room
                break

        if not assigned_room:
            return RoomBookingServiceResult(
                success=False,
                message_it="Nessuna camera fisica libera trovata per la categoria selezionata.",
            )

        nights = avail.nights
        total_price = round(assigned_room.price_per_night * nights, 2)

        # Generate unique reference code with collision check
        ref_code = generate_reference_code()
        attempts = 0
        while await self.room_repo.get_booking_by_ref(ref_code) is not None:
            attempts += 1
            if attempts > 10:
                ref_code = f"SINA-{uuid.uuid4().hex[:8].upper()}"
                if await self.room_repo.get_booking_by_ref(ref_code) is None:
                    break
            else:
                ref_code = generate_reference_code()

        booking = RoomBooking(
            id=f"book_{uuid.uuid4().hex[:10]}",
            reference_code=ref_code,
            hotel_id=self.hotel_id,
            guest_name=request.guest_name,
            guest_phone=request.guest_phone,
            guest_email=request.guest_email,
            room_number=assigned_room.room_number,
            room_category=request.category,
            check_in_date=request.check_in_date,
            check_out_date=request.check_out_date,
            nights=nights,
            guests_count=request.guests_count,
            price_per_night=assigned_room.price_per_night,
            total_price=total_price,
            special_requests=request.special_requests,
            is_early_check_in=request.is_early_check_in,
            status=RoomBookingStatus.CONFIRMED,
        )

        saved_booking = await self.room_repo.create_booking(booking)

        # Notify Front Desk & Concierge
        early_note = " (Richiesto Early Check-in)" if request.is_early_check_in else ""
        notif_msg = (
            f"Nuova prenotazione {ref_code}: {saved_booking.guest_name} ({saved_booking.guest_phone}). "
            f"Camera {assigned_room.room_number} ({ROOM_CATEGORY_DETAILS[request.category]['name_it']}) "
            f"dal {request.check_in_date.strftime('%d/%m/%Y')} al {request.check_out_date.strftime('%d/%m/%Y')} "
            f"({nights} notti, {request.guests_count} ospiti). Totale: €{total_price:.2f}.{early_note}"
        )
        if request.special_requests:
            notif_msg += f" Note: {request.special_requests}."

        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=self.hotel_id,
            type=NotificationType.NEW_BOOKING,
            title=f"Nuova Prenotazione Camera {ref_code} - {saved_booking.guest_name}",
            message=notif_msg,
            customer_name=saved_booking.guest_name,
            customer_phone=saved_booking.guest_phone,
            reference_code=ref_code,
        )
        await self.notification_repo.add_notification(notif)

        cat_name = ROOM_CATEGORY_DETAILS[request.category]["name_it"]

        # Dispatch automated SMS confirmation if Twilio service is present
        if self.twilio_service and saved_booking.guest_phone:
            try:
                await self.twilio_service.send_booking_confirmation_sms(
                    to_phone=saved_booking.guest_phone,
                    guest_name=saved_booking.guest_name,
                    reference_code=ref_code,
                    category=cat_name,
                    check_in_date=request.check_in_date.isoformat(),
                    check_out_date=request.check_out_date.isoformat(),
                )
            except Exception:
                pass

        # Dispatch automated Email confirmation if email was captured
        if self.email_service and saved_booking.guest_email:
            try:
                await self.email_service.send_room_booking_confirmation(
                    to_email=saved_booking.guest_email,
                    guest_name=saved_booking.guest_name,
                    reference_code=ref_code,
                    room_category=cat_name,
                    check_in_date=request.check_in_date.isoformat(),
                    check_out_date=request.check_out_date.isoformat(),
                    guests_count=request.guests_count,
                    total_price=int(total_price),
                    room_number=assigned_room.room_number,
                    special_requests=request.special_requests,
                )
            except Exception:
                pass

        # Sync to Guest CRM if service provided
        if self.guest_crm_service:
            await self.guest_crm_service.save_guest_preference(
                phone=saved_booking.guest_phone,
                special_note=f"Prenotazione {ref_code}: camera {assigned_room.room_number} {cat_name}.",
            )
        success_msg = (
            f"La Sua prenotazione è confermata con codice {ref_code}! "
            f"Abbiamo riservato la {cat_name} (camera {assigned_room.room_number}) "
            f"dal {request.check_in_date.strftime('%d/%m/%Y')} al {request.check_out_date.strftime('%d/%m/%Y')} "
            f"per {request.guests_count} ospiti. Importo totale soggiorno: €{total_price:.2f}. "
            "Riceverà a breve il riepilogo via SMS/messaggio."
        )

        return RoomBookingServiceResult(
            success=True,
            message_it=success_msg,
            booking=saved_booking,
        )

    async def modify_booking(
        self, request: ModifyRoomBookingRequest
    ) -> RoomBookingServiceResult:
        booking = await self.room_repo.get_booking_by_ref(request.reference_code)
        if not booking:
            return RoomBookingServiceResult(
                success=False,
                message_it=f"Nessuna prenotazione trovata con il codice {request.reference_code}.",
            )

        # Phone verification
        clean_req_phone = request.guest_phone.replace(" ", "").replace("-", "")
        clean_book_phone = booking.guest_phone.replace(" ", "").replace("-", "")
        if clean_req_phone != clean_book_phone:
            return RoomBookingServiceResult(
                success=False,
                message_it="Il numero di telefono non corrisponde ai dati registrati per questa prenotazione.",
            )

        new_in = request.new_check_in_date or booking.check_in_date
        new_out = request.new_check_out_date or booking.check_out_date
        new_cat = request.new_category or booking.room_category
        new_guests = request.new_guests_count or booking.guests_count

        # Check availability if dates or category changed
        if (
            new_in != booking.check_in_date
            or new_out != booking.check_out_date
            or new_cat != booking.room_category
        ):
            avail = await self.check_availability(new_in, new_out, new_guests, new_cat)
            if not avail.is_available:
                return RoomBookingServiceResult(
                    success=False,
                    message_it="Le nuove date o categoria richieste non sono disponibili.",
                )

        nights = (new_out - new_in).days
        price_per_night = ROOM_CATEGORY_DETAILS[new_cat]["price_per_night"]
        total_price = round(price_per_night * nights, 2)

        booking.check_in_date = new_in
        booking.check_out_date = new_out
        booking.room_category = new_cat
        booking.guests_count = new_guests
        booking.nights = nights
        booking.price_per_night = price_per_night
        booking.total_price = total_price
        if request.new_special_requests:
            booking.special_requests = request.new_special_requests
        booking.updated_at = datetime.now(UTC)

        updated_booking = await self.room_repo.update_booking(booking)

        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=self.hotel_id,
            type=NotificationType.MODIFICATION,
            title=f"Modifica Prenotazione Camera {booking.reference_code} - {booking.guest_name}",
            message=f"Date aggiornate: {new_in.strftime('%d/%m/%Y')} - {new_out.strftime('%d/%m/%Y')} ({nights} notti, €{total_price:.2f}).",
            customer_name=booking.guest_name,
            customer_phone=booking.guest_phone,
            reference_code=booking.reference_code,
        )
        await self.notification_repo.add_notification(notif)

        return RoomBookingServiceResult(
            success=True,
            message_it=f"La prenotazione {booking.reference_code} è stata aggiornata con successo.",
            booking=updated_booking,
        )

    async def cancel_booking(
        self, reference_code: str, guest_phone: str, reason: str | None = None
    ) -> RoomBookingServiceResult:
        booking = await self.room_repo.get_booking_by_ref(reference_code)
        if not booking:
            return RoomBookingServiceResult(
                success=False,
                message_it=f"Nessuna prenotazione trovata con il codice {reference_code}.",
            )

        clean_req_phone = guest_phone.replace(" ", "").replace("-", "")
        clean_book_phone = booking.guest_phone.replace(" ", "").replace("-", "")
        if clean_req_phone != clean_book_phone:
            return RoomBookingServiceResult(
                success=False,
                message_it="Il numero di telefono non corrisponde alla prenotazione indicata.",
            )

        booking.status = RoomBookingStatus.CANCELLED
        booking.updated_at = datetime.now(UTC)
        updated_booking = await self.room_repo.update_booking(booking)

        reason_str = f" Motivo: {reason}" if reason else ""
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=self.hotel_id,
            type=NotificationType.CANCELLATION,
            title=f"Cancellazione Prenotazione {booking.reference_code} - {booking.guest_name}",
            message=f"La prenotazione per la camera {booking.room_number} è stata cancellata.{reason_str}",
            customer_name=booking.guest_name,
            customer_phone=booking.guest_phone,
            reference_code=booking.reference_code,
        )
        await self.notification_repo.add_notification(notif)

        return RoomBookingServiceResult(
            success=True,
            message_it=f"La prenotazione {booking.reference_code} è stata cancellata come da Lei richiesto.",
            booking=updated_booking,
        )

    async def mark_early_departure(
        self, request: MarkEarlyDepartureRequest
    ) -> RoomBookingServiceResult:
        booking = await self.room_repo.get_booking_by_ref(request.reference_code)
        if not booking:
            return RoomBookingServiceResult(
                success=False,
                message_it=f"Nessuna prenotazione trovata con il codice {request.reference_code}.",
            )

        clean_req_phone = request.guest_phone.replace(" ", "").replace("-", "")
        clean_book_phone = booking.guest_phone.replace(" ", "").replace("-", "")
        if clean_req_phone != clean_book_phone:
            return RoomBookingServiceResult(
                success=False,
                message_it="Il numero di telefono non corrisponde all'ospite registrato.",
            )

        dep_date = request.actual_departure_date or date.today()
        booking.is_early_departure = True
        booking.actual_departure_date = dep_date
        booking.early_departure_reason = request.reason or "Partenza anticipata segnalata dall'ospite"
        booking.status = RoomBookingStatus.EARLY_DEPARTURE

        # Recalculate nights and cost based on actual stay duration
        actual_nights = max(1, (dep_date - booking.check_in_date).days)
        booking.nights = actual_nights
        booking.total_price = round(booking.price_per_night * actual_nights, 2)
        booking.updated_at = datetime.now(UTC)

        updated_booking = await self.room_repo.update_booking(booking)

        # Notify Housekeeping and Front Desk immediately
        notif = CRMNotification(
            id=str(uuid.uuid4()),
            restaurant_id=self.hotel_id,
            type=NotificationType.CONCIERGE_REQUEST,
            title=f"Partenza Anticipata (Early Departure) - Camera {booking.room_number} ({booking.guest_name})",
            message=(
                f"L'ospite in camera {booking.room_number} ({booking.guest_name}) ha effettuato la partenza anticipata in data {dep_date.strftime('%d/%m/%Y')}. "
                f"Motivo: {booking.early_departure_reason}. Avvisare Governante per pulizia camera e Reception per conto."
            ),
            customer_name=booking.guest_name,
            customer_phone=booking.guest_phone,
            reference_code=booking.reference_code,
        )
        await self.notification_repo.add_notification(notif)

        return RoomBookingServiceResult(
            success=True,
            message_it=(
                f"Abbiamo registrato la Sua partenza anticipata per la camera {booking.room_number}. "
                f"Il conto è stato aggiornato per {actual_nights} notti (totale: €{booking.total_price:.2f}). "
                "Grazie per essere stato nostro ospite a Sina Hotels."
            ),
            booking=updated_booking,
        )

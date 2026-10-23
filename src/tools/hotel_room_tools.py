import json
from datetime import date

from src.tools.base import BaseTool
from pydantic import BaseModel, Field

from src.models.hotel_booking import (
    CreateRoomBookingRequest,
    MarkEarlyDepartureRequest,
    ModifyRoomBookingRequest,
    RoomCategory,
)
from src.services.hotel_booking_service import HotelBookingService


class CheckRoomAvailabilityInput(BaseModel):
    check_in_date: str = Field(
        description="Data di arrivo/check-in in formato YYYY-MM-DD (es. '2026-10-24')"
    )
    check_out_date: str = Field(
        description="Data di partenza/check-out in formato YYYY-MM-DD (es. '2026-10-27')"
    )
    guests_count: int = Field(
        default=2,
        description="Numero totale di ospiti (adulti e ragazzi, max 4)",
    )
    category: str | None = Field(
        default=None,
        description="Categoria opzionale richiesta: 'superior', 'deluxe', 'junior_suite', 'panoramic_suite'",
    )


class CheckRoomAvailabilityTool(BaseTool):
    name: str = "check_room_availability"
    description: str = (
        "Verifica in tempo reale la disponibilità effettiva delle camere di Sina Hotels per le date indicate. "
        "Restituisce le tipologie disponibili (Superior €250, Deluxe €350, Junior Suite €480, Suite Panoramica €750), "
        "il numero di notti e il prezzo totale."
    )
    args_schema: type[BaseModel] = CheckRoomAvailabilityInput
    booking_service: HotelBookingService

    async def _arun(
        self,
        check_in_date: str,
        check_out_date: str,
        guests_count: int = 2,
        category: str | None = None,
    ) -> str:
        try:
            d_in = date.fromisoformat(check_in_date.strip())
            d_out = date.fromisoformat(check_out_date.strip())
        except ValueError:
            return json.dumps(
                {
                    "is_available": False,
                    "message_it": "Formato data non valido. Usare il formato YYYY-MM-DD (es. 2026-10-24).",
                },
                ensure_ascii=False,
            )

        cat_enum = None
        if category:
            try:
                cat_enum = RoomCategory(category.strip().lower())
            except ValueError:
                pass

        res = await self.booking_service.check_availability(
            check_in_date=d_in,
            check_out_date=d_out,
            guests_count=guests_count,
            category=cat_enum,
        )
        return json.dumps(res.model_dump(mode="json"), ensure_ascii=False)

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class CreateHotelRoomBookingInput(BaseModel):
    guest_name: str = Field(description="Nome e cognome completo dell'ospite")
    guest_phone: str = Field(description="Numero di telefono cellulare dell'ospite")
    category: str = Field(
        description="Categoria camera scelta: 'superior', 'deluxe', 'junior_suite', 'panoramic_suite'"
    )
    check_in_date: str = Field(
        description="Data di arrivo (check-in) in formato YYYY-MM-DD"
    )
    check_out_date: str = Field(
        description="Data di partenza (check-out) in formato YYYY-MM-DD"
    )
    guests_count: int = Field(default=2, description="Numero di ospiti")
    special_requests: str | None = Field(
        default=None,
        description="Richieste speciali (es. letto matrimoniale, piano alto, culla, allergie)",
    )
    is_early_check_in: bool = Field(
        default=False,
        description="True se l'ospite richiede arrivo anticipato prima delle 15:00",
    )


class CreateHotelRoomBookingTool(BaseTool):
    name: str = "create_hotel_room_booking"
    description: str = (
        "Crea e conferma una prenotazione per una camera a Sina Hotels assegnando il numero di camera "
        "e generando il codice di conferma (es. SINA-1042). Salva i dettagli nel CRM e notifica la reception."
    )
    args_schema: type[BaseModel] = CreateHotelRoomBookingInput
    booking_service: HotelBookingService

    async def _arun(
        self,
        guest_name: str,
        guest_phone: str,
        category: str,
        check_in_date: str,
        check_out_date: str,
        guests_count: int = 2,
        special_requests: str | None = None,
        is_early_check_in: bool = False,
    ) -> str:
        try:
            d_in = date.fromisoformat(check_in_date.strip())
            d_out = date.fromisoformat(check_out_date.strip())
            cat_enum = RoomCategory(category.strip().lower())
        except (ValueError, KeyError):
            return json.dumps(
                {
                    "success": False,
                    "message_it": "Parametri non validi per la prenotazione (verificare date o tipologia camera).",
                },
                ensure_ascii=False,
            )

        req = CreateRoomBookingRequest(
            guest_name=guest_name.strip(),
            guest_phone=guest_phone.strip(),
            category=cat_enum,
            check_in_date=d_in,
            check_out_date=d_out,
            guests_count=guests_count,
            special_requests=special_requests,
            is_early_check_in=is_early_check_in,
        )
        result = await self.booking_service.create_booking(req)
        return json.dumps(
            {
                "success": result.success,
                "message_it": result.message_it,
                "reference_code": result.booking.reference_code if result.booking else None,
                "room_number": result.booking.room_number if result.booking else None,
                "total_price": result.booking.total_price if result.booking else None,
            },
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class ModifyHotelRoomBookingInput(BaseModel):
    reference_code: str = Field(
        description="Codice prenotazione (es. SINA-4020) fornito dall'ospite"
    )
    guest_phone: str = Field(description="Numero di telefono per verifica identità")
    new_check_in_date: str | None = Field(
        default=None, description="Nuova data di arrivo YYYY-MM-DD se modificata"
    )
    new_check_out_date: str | None = Field(
        default=None, description="Nuova data di partenza YYYY-MM-DD se modificata"
    )
    new_category: str | None = Field(
        default=None, description="Nuova categoria se richiesta (superior, deluxe, etc.)"
    )
    new_guests_count: int | None = Field(
        default=None, description="Nuovo numero di ospiti"
    )
    new_special_requests: str | None = Field(
        default=None, description="Nuove note o richieste"
    )


class ModifyHotelRoomBookingTool(BaseTool):
    name: str = "modify_hotel_room_booking"
    description: str = (
        "Modifica date, tipologia o numero ospiti di una prenotazione esistente dopo aver verificato "
        "il codice prenotazione e il recapito telefonico."
    )
    args_schema: type[BaseModel] = ModifyHotelRoomBookingInput
    booking_service: HotelBookingService

    async def _arun(
        self,
        reference_code: str,
        guest_phone: str,
        new_check_in_date: str | None = None,
        new_check_out_date: str | None = None,
        new_category: str | None = None,
        new_guests_count: int | None = None,
        new_special_requests: str | None = None,
    ) -> str:
        d_in = date.fromisoformat(new_check_in_date.strip()) if new_check_in_date else None
        d_out = date.fromisoformat(new_check_out_date.strip()) if new_check_out_date else None
        cat_enum = RoomCategory(new_category.strip().lower()) if new_category else None

        req = ModifyRoomBookingRequest(
            reference_code=reference_code.strip(),
            guest_phone=guest_phone.strip(),
            new_check_in_date=d_in,
            new_check_out_date=d_out,
            new_category=cat_enum,
            new_guests_count=new_guests_count,
            new_special_requests=new_special_requests,
        )
        res = await self.booking_service.modify_booking(req)
        return json.dumps(
            {"success": res.success, "message_it": res.message_it},
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class CancelHotelRoomBookingInput(BaseModel):
    reference_code: str = Field(description="Codice prenotazione (es. SINA-4020)")
    guest_phone: str = Field(description="Numero di telefono per verifica identità")
    reason: str | None = Field(
        default=None, description="Motivo espresso dall'ospite per la cancellazione"
    )


class CancelHotelRoomBookingTool(BaseTool):
    name: str = "cancel_hotel_room_booking"
    description: str = (
        "Cancella una prenotazione camera a Sina Hotels previa verifica del codice di prenotazione "
        "e del numero di telefono dell'ospite. Rilascia la camera nel sistema."
    )
    args_schema: type[BaseModel] = CancelHotelRoomBookingInput
    booking_service: HotelBookingService

    async def _arun(
        self, reference_code: str, guest_phone: str, reason: str | None = None
    ) -> str:
        res = await self.booking_service.cancel_booking(
            reference_code=reference_code.strip(),
            guest_phone=guest_phone.strip(),
            reason=reason,
        )
        return json.dumps(
            {"success": res.success, "message_it": res.message_it},
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class ReportEarlyDepartureInput(BaseModel):
    reference_code: str = Field(description="Codice prenotazione (es. SINA-1018)")
    guest_phone: str = Field(description="Numero di telefono dell'ospite")
    reason: str | None = Field(
        default=None,
        description="Motivo della partenza anticipata (es. 'urgenza aziendale', 'rientro anticipato')",
    )


class ReportEarlyDepartureTool(BaseTool):
    name: str = "report_early_departure"
    description: str = (
        "Registra la partenza anticipata (Early Departure) di un ospite che lascia la camera prima "
        "del check-out originariamente previsto. Ricalcola il conto, libera la camera e avvisa la governante e la reception."
    )
    args_schema: type[BaseModel] = ReportEarlyDepartureInput
    booking_service: HotelBookingService

    async def _arun(
        self, reference_code: str, guest_phone: str, reason: str | None = None
    ) -> str:
        req = MarkEarlyDepartureRequest(
            reference_code=reference_code.strip(),
            guest_phone=guest_phone.strip(),
            actual_departure_date=date.today(),
            reason=reason,
        )
        res = await self.booking_service.mark_early_departure(req)
        return json.dumps(
            {
                "success": res.success,
                "message_it": res.message_it,
                "actual_departure_date": str(date.today()),
            },
            ensure_ascii=False,
        )

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class HotelInfoAndServicesInput(BaseModel):
    topic: str = Field(
        description="Argomento: 'checkin_checkout', 'colazione', 'spa', 'rooftop', 'parcheggio', 'indirizzo'"
    )


class HotelInfoAndServicesTool(BaseTool):
    name: str = "get_hotel_services_info"
    description: str = (
        "Fornisce informazioni ufficiali sui servizi e orari di Sina Bernini Bristol: "
        "orari check-in (15:00) e check-out (12:00), colazione (07:00-10:30), "
        "Rooftop The Flair, Sina Wellness Spa, palestra, garage e posizione."
    )
    args_schema: type[BaseModel] = HotelInfoAndServicesInput

    async def _arun(self, topic: str) -> str:
        info = {
            "checkin_checkout": "Il check-in è disponibile dalle ore 15:00. Il check-out è entro le ore 12:00. Late check-out o early check-in disponibili su richiesta.",
            "colazione": "La colazione a buffet gourmet viene servita nel Salone Bernini o in camera dalle 07:00 alle 10:30 con ampia scelta dolce, salata e opzioni senza glutine.",
            "spa": "La Sina Wellness & Spa è aperta dalle 10:00 alle 20:00 su appuntamento, con sauna, bagno turco, idromassaggio e trattamenti corpo esclusivi.",
            "rooftop": "Il Rooftop Restaurant 'The Flair' all'ultimo piano offre cena gourmet con vista panoramica a 360° su Roma dalle 19:30 alle 23:00. Il Bar del Bristol è aperto dalle 10:30 alle 00:30.",
            "parcheggio": "Disponiamo di servizio Car Valet privato e convenzione con garage custodito con ricarica per veicoli elettrici.",
            "indirizzo": "Sina Bernini Bristol si trova in Piazza Barberini 23, 00187 Roma, proprio di fronte alla Fontana del Tritone e all'inizio di Via Veneto.",
        }
        key = topic.strip().lower()
        ans = info.get(key, info["checkin_checkout"])
        return json.dumps({"topic": key, "info_it": ans}, ensure_ascii=False)

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


class EndCallInput(BaseModel):
    farewell_message: str | None = Field(
        default=None, description="Messaggio finale di commiato in italiano formale"
    )


class EndCallTool(BaseTool):
    name: str = "end_call"
    description: str = (
        "Chiude formalmente la telefonata e riaggancia quando l'ospite ha completato tutte le sue richieste "
        "e conferma che non ha bisogno di altro (es. 'No grazie', 'A posto così', 'Arrivederci')."
    )
    args_schema: type[BaseModel] = EndCallInput

    async def _arun(self, farewell_message: str | None = None) -> str:
        msg = farewell_message or "Arrivederci da Sina Hotels e a presto!"
        return f"CHIAMATA_TERMINATA: {msg}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async execution")


def build_hotel_room_tools(booking_service: HotelBookingService) -> list[BaseTool]:
    return [
        CheckRoomAvailabilityTool(booking_service=booking_service),
        CreateHotelRoomBookingTool(booking_service=booking_service),
        ModifyHotelRoomBookingTool(booking_service=booking_service),
        CancelHotelRoomBookingTool(booking_service=booking_service),
        ReportEarlyDepartureTool(booking_service=booking_service),
        HotelInfoAndServicesTool(),
        EndCallTool(),
    ]

from datetime import date

from pydantic import BaseModel, Field

from src.models import (
    CancelReservationRequest,
    CreateReservationRequest,
    ModifyReservationRequest,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.tools.base import BaseTool


class CheckAvailabilityInput(BaseModel):
    booking_date: str = Field(description="Data richiesta in formato YYYY-MM-DD (es. '2026-10-23')")
    booking_time: str = Field(
        description="Orario richiesto in formato HH:MM (es. '20:00' o '13:30')"
    )
    party_size: int = Field(description="Numero di persone (es. 2 o 4)")


class CreateReservationInput(BaseModel):
    customer_name: str = Field(description="Nome e cognome del cliente")
    customer_phone: str = Field(description="Numero di telefono del cliente")
    party_size: int = Field(description="Numero di persone")
    booking_date: str = Field(description="Data in formato YYYY-MM-DD (es. '2026-10-23')")
    booking_time: str = Field(description="Orario in formato HH:MM (es. '20:00' o '13:30')")
    dietary_notes: str | None = Field(
        default=None,
        description="Eventuali allergie o intolleranze (es. 'celiachia', 'senza glutine', 'vegetariano')",
    )
    special_requests: str | None = Field(
        default=None,
        description="Richieste speciali (es. 'tavolo appartato', 'seggiolone per bambino')",
    )


class ModifyReservationInput(BaseModel):
    reference_code: str | None = Field(
        default=None,
        description="Codice di prenotazione (es. 'BV-1234') se fornito dal cliente",
    )
    customer_phone: str = Field(description="Numero di telefono del cliente per verifica")
    customer_name: str | None = Field(
        default=None, description="Nome o cognome del cliente per verifica"
    )
    new_date: str | None = Field(
        default=None, description="Nuova data in formato YYYY-MM-DD se modificata"
    )
    new_time: str | None = Field(
        default=None, description="Nuovo orario in formato HH:MM se modificato"
    )
    new_party_size: int | None = Field(
        default=None, description="Nuovo numero di persone se modificato"
    )
    new_dietary_notes: str | None = Field(
        default=None, description="Nuove note dietetiche o allergie se modificate"
    )


class CancelReservationInput(BaseModel):
    reference_code: str | None = Field(
        default=None,
        description="Codice di prenotazione (es. 'BV-1234') se fornito dal cliente",
    )
    customer_phone: str = Field(description="Numero di telefono del cliente per verifica")
    customer_name: str | None = Field(
        default=None, description="Nome o cognome del cliente per verifica"
    )
    reason: str | None = Field(default=None, description="Motivo della cancellazione se comunicato")


class RestaurantFAQInput(BaseModel):
    query: str = Field(
        description="Domanda su orari, parcheggio, animali, allergeni, indirizzo o menu"
    )


class OwnerMessageInput(BaseModel):
    caller_name: str = Field(description="Nome del chiamante")
    caller_phone: str = Field(description="Numero di telefono del chiamante")
    message_body: str = Field(description="Contenuto del messaggio per il titolare")


class EndCallInput(BaseModel):
    farewell_message: str | None = Field(
        default=None,
        description="Messaggio finale di commiato (es. 'La ringrazio e Le auguro una buona giornata. Arrivederci!')",
    )


def build_tools(
    restaurant_id: str,
    availability_service: AvailabilityService,
    booking_service: BookingService,
    restaurant_service: RestaurantService,
    notification_service: NotificationService,
):
    class CheckAvailabilityTool(BaseTool):
        name: str = "check_table_availability"
        description: str = (
            "Verifica la disponibilità reale dei tavoli per una specifica data, orario e numero di persone. "
            "Restituisce esito positivo oppure motivazione e orari alternativi suggeriti."
        )
        args_schema: type[BaseModel] = CheckAvailabilityInput

        def _run(self, *args, **kwargs):
            raise NotImplementedError("Use async execution")

        async def _arun(self, booking_date: str, booking_time: str, party_size: int) -> str:
            try:
                parsed_date = date.fromisoformat(booking_date)
            except ValueError:
                return "Errore: data non valida. Usa YYYY-MM-DD."
            resp = await availability_service.check_availability(
                restaurant_id=restaurant_id,
                booking_date=parsed_date,
                booking_time_str=booking_time,
                party_size=party_size,
            )
            if resp.is_available:
                return (
                    f"DISPONIBILE: Tavolo disponibile per {party_size} persone in data "
                    f"{parsed_date.strftime('%d/%m/%Y')} alle {booking_time}."
                )
            alt_text = ""
            if resp.alternatives:
                alt_text = f" Orari alternativi disponibili: {', '.join(resp.alternatives)}."
            return f"NON DISPONIBILE: {resp.reason}{alt_text}"

    class CreateReservationTool(BaseTool):
        name: str = "create_reservation"
        description: str = (
            "Crea definitivamente una prenotazione nel gestionale. Esegui questo strumento solo dopo aver verificato "
            "la disponibilità e aver raccolto tutti i dettagli obbligatori: nome, telefono, data, ora e coperti."
        )
        args_schema: type[BaseModel] = CreateReservationInput

        def _run(self, *args, **kwargs):
            raise NotImplementedError("Use async execution")

        async def _arun(
            self,
            customer_name: str,
            customer_phone: str,
            party_size: int,
            booking_date: str,
            booking_time: str,
            dietary_notes: str | None = None,
            special_requests: str | None = None,
        ) -> str:
            try:
                parsed_date = date.fromisoformat(booking_date)
            except ValueError:
                return "Errore: formato data non valido."

            req = CreateReservationRequest(
                customer_name=customer_name,
                customer_phone=customer_phone,
                party_size=party_size,
                booking_date=parsed_date,
                booking_time=booking_time,
                dietary_notes=dietary_notes,
                special_requests=special_requests,
            )
            result = await booking_service.create_booking(restaurant_id, req)
            return result.message_it

    class ModifyReservationTool(BaseTool):
        name: str = "modify_reservation"
        description: str = (
            "Modifica una prenotazione esistente (data, orario, numero coperti o note). "
            "Richiede il telefono del cliente e, se disponibile, il codice prenotazione o cognome per verifica."
        )
        args_schema: type[BaseModel] = ModifyReservationInput

        def _run(self, *args, **kwargs):
            raise NotImplementedError("Use async execution")

        async def _arun(
            self,
            customer_phone: str,
            reference_code: str | None = None,
            customer_name: str | None = None,
            new_date: str | None = None,
            new_time: str | None = None,
            new_party_size: int | None = None,
            new_dietary_notes: str | None = None,
        ) -> str:
            parsed_date = None
            if new_date:
                try:
                    parsed_date = date.fromisoformat(new_date)
                except ValueError:
                    return "Errore: formato data non valido."

            req = ModifyReservationRequest(
                reference_code=reference_code or "",
                customer_phone=customer_phone,
                customer_name=customer_name,
                new_date=parsed_date,
                new_time=new_time,
                new_party_size=new_party_size,
                new_dietary_notes=new_dietary_notes,
            )
            result = await booking_service.modify_booking(restaurant_id, req)
            return result.message_it

    class CancelReservationTool(BaseTool):
        name: str = "cancel_reservation"
        description: str = (
            "Cancella una prenotazione esistente su richiesta del cliente. "
            "Richiede il telefono del cliente e, se possibile, il codice prenotazione o cognome per verifica."
        )
        args_schema: type[BaseModel] = CancelReservationInput

        def _run(self, *args, **kwargs):
            raise NotImplementedError("Use async execution")

        async def _arun(
            self,
            customer_phone: str,
            reference_code: str | None = None,
            customer_name: str | None = None,
            reason: str | None = None,
        ) -> str:
            req = CancelReservationRequest(
                reference_code=reference_code or "",
                customer_phone=customer_phone,
                customer_name=customer_name,
                reason=reason,
            )
            result = await booking_service.cancel_booking(restaurant_id, req)
            return result.message_it

    class RestaurantFAQTool(BaseTool):
        name: str = "get_restaurant_faq_or_hours"
        description: str = (
            "Risponde a domande frequenti sul ristorante: orari di apertura, turni pranzo/cena, parcheggio, "
            "animali domestici, opzioni per celiaci/allergie e posizione."
        )
        args_schema: type[BaseModel] = RestaurantFAQInput

        def _run(self, *args, **kwargs):
            raise NotImplementedError("Use async execution")

        async def _arun(self, query: str) -> str:
            query_lower = query.lower()
            if "orari" in query_lower or "apert" in query_lower or "chius" in query_lower:
                return await restaurant_service.get_opening_hours_text(restaurant_id)
            ans = await restaurant_service.answer_faq(restaurant_id, query)
            if ans:
                return ans
            # Fallback to general hours
            return await restaurant_service.get_opening_hours_text(restaurant_id)

    class OwnerMessageTool(BaseTool):
        name: str = "leave_message_for_owner"
        description: str = (
            "Invia una notifica al titolare o responsabile di sala con un messaggio o richiesta speciale del cliente "
            "(es. eventi privati, gruppi numerosi oltre 10 persone, richieste non gestibili in autonomia)."
        )
        args_schema: type[BaseModel] = OwnerMessageInput

        def _run(self, *args, **kwargs):
            raise NotImplementedError("Use async execution")

        async def _arun(self, caller_name: str, caller_phone: str, message_body: str) -> str:
            await notification_service.notify_owner_message(
                restaurant_id=restaurant_id,
                caller_name=caller_name,
                caller_phone=caller_phone,
                message_body=message_body,
            )
            return (
                f"Messaggio registrato con successo nel sistema del ristorante per il titolare a nome {caller_name}. "
                "Il nostro staff La ricontatterà al più presto."
            )

    class EndCallTool(BaseTool):
        name: str = "end_call"
        description: str = (
            "Chiude formalmente la telefonata e riaggancia il ricevitore quando il cliente ha completato tutte le sue richieste "
            "e conferma che non ha bisogno di altro (es. risponde 'No grazie', 'A posto così', 'Niente altro', 'Arrivederci')."
        )
        args_schema: type[BaseModel] = EndCallInput

        def _run(self, *args, **kwargs):
            raise NotImplementedError("Use async execution")

        async def _arun(self, farewell_message: str | None = None) -> str:
            msg = farewell_message or "Arrivederci e a presto!"
            return f"CHIAMATA_TERMINATA: {msg}"

    return [
        CheckAvailabilityTool(),
        CreateReservationTool(),
        ModifyReservationTool(),
        CancelReservationTool(),
        RestaurantFAQTool(),
        OwnerMessageTool(),
        EndCallTool(),
    ]

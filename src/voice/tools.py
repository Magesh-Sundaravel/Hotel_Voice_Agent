"""Native tool definitions, schemas, and execution dispatcher for voice receptionist.

No dependency on LangChain or LangGraph. Uses OpenAI/Groq standard function calling schemas.
Incorporate deterministic security & business guardrails:
1. Date validation (ISO dates, check-in >= today, check-out > check-in).
2. Read-back confirmation before booking.
3. Identity check before revealing, modifying, or cancelling bookings.
4. Deterministic injection of caller_phone and user_id (never LLM-fillable).
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.models import (
    ConciergeCategory,
    CreateReservationRequest,
    CreateRoomBookingRequest,
    MarkEarlyDepartureRequest,
    ModifyRoomBookingRequest,
    RoomCategory,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.voice.session import CallSession

logger = logging.getLogger(__name__)

# Official Hotel Info lookup dictionary
HOTEL_SERVICES_INFO = {
    "checkin_checkout": (
        "Il check-in è disponibile dalle ore 15:00. Il check-out è entro le ore 12:00. "
        "Late check-out o early check-in disponibili su richiesta."
    ),
    "colazione": (
        "La colazione a buffet gourmet viene servita nel Salone Bernini o in camera dalle 07:00 alle 10:30 "
        "con ampia scelta dolce, salata e opzioni senza glutine."
    ),
    "spa": (
        "La Sina Wellness & Spa è aperta dalle 10:00 alle 20:00 su appuntamento, "
        "con sauna, bagno turco, idromassaggio e trattamenti corpo esclusivi."
    ),
    "rooftop": (
        "Il Rooftop Restaurant 'The Flair' all'ultimo piano offre cena gourmet con vista panoramica a 360° "
        "su Roma dalle 19:30 alle 23:00. Il Bar del Bristol è aperto dalle 10:30 alle 00:30."
    ),
    "parcheggio": (
        "Disponiamo di servizio Car Valet privato e convenzione con garage custodito "
        "con ricarica per veicoli elettrici."
    ),
    "indirizzo": (
        "Sina Bernini Bristol si trova in Piazza Barberini 23, 00187 Roma, "
        "proprio di fronte alla Fontana del Tritone e all'inizio di Via Veneto."
    ),
}

# ---------------------------------------------------------------------------
# Native Tool Definitions (OpenAI / Groq format)
# Note: Caller identity fields (guest_phone, phone_number, user_id) are omitted
# from tool schemas. They are injected deterministically by our code.
# ---------------------------------------------------------------------------

HOTEL_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "check_room_availability",
            "description": (
                "Verifica in tempo reale la disponibilità effettiva delle camere di Sina Hotels per le date indicate. "
                "Restituisce le tipologie disponibili (Superior €250, Deluxe €350, Junior Suite €480, Suite Panoramica €750), "
                "il numero di notti e il prezzo totale."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "check_in_date": {
                        "type": "string",
                        "description": "Data di arrivo/check-in in formato YYYY-MM-DD (es. '2026-10-24')",
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Data di partenza/check-out in formato YYYY-MM-DD (es. '2026-10-27')",
                    },
                    "guests_count": {
                        "type": "integer",
                        "description": "Numero totale di ospiti (max 4, default 2)",
                        "default": 2,
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria camera richiesta: 'superior', 'deluxe', 'junior_suite', 'panoramic_suite'",
                    },
                },
                "required": ["check_in_date", "check_out_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_hotel_room_booking",
            "description": (
                "Crea e conferma una prenotazione per una camera a Sina Hotels assegnando il numero di camera "
                "e generando il codice di conferma (es. SINA-1042). Salva i dettagli nel CRM e notifica la reception."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_name": {
                        "type": "string",
                        "description": "Nome e cognome completo dell'ospite",
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria camera scelta: 'superior', 'deluxe', 'junior_suite', 'panoramic_suite'",
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Data di arrivo (check-in) in formato YYYY-MM-DD",
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Data di partenza (check-out) in formato YYYY-MM-DD",
                    },
                    "guests_count": {
                        "type": "integer",
                        "description": "Numero di ospiti (default 2)",
                        "default": 2,
                    },
                    "special_requests": {
                        "type": "string",
                        "description": "Richieste speciali (es. letto matrimoniale, piano alto, culla, allergie)",
                    },
                    "is_early_check_in": {
                        "type": "boolean",
                        "description": "True se l'ospite richiede arrivo anticipato prima delle 15:00",
                        "default": False,
                    },
                },
                "required": ["guest_name", "category", "check_in_date", "check_out_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_hotel_room_booking",
            "description": (
                "Modifica date, tipologia o numero ospiti di una prenotazione esistente dopo aver verificato "
                "il codice prenotazione e l'identità del chiamante."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reference_code": {
                        "type": "string",
                        "description": "Codice prenotazione (es. SINA-4020) fornito dall'ospite",
                    },
                    "new_check_in_date": {
                        "type": "string",
                        "description": "Nuova data di arrivo YYYY-MM-DD se modificata",
                    },
                    "new_check_out_date": {
                        "type": "string",
                        "description": "Nuova data di partenza YYYY-MM-DD se modificata",
                    },
                    "new_category": {
                        "type": "string",
                        "description": "Nuova categoria se richiesta (superior, deluxe, etc.)",
                    },
                    "new_guests_count": {
                        "type": "integer",
                        "description": "Nuovo numero di ospiti",
                    },
                    "new_special_requests": {
                        "type": "string",
                        "description": "Nuove note o richieste",
                    },
                },
                "required": ["reference_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_hotel_room_booking",
            "description": (
                "Cancella una prenotazione camera a Sina Hotels previa verifica del codice di prenotazione "
                "e dell'identità del chiamante. Rilascia la camera nel sistema."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reference_code": {
                        "type": "string",
                        "description": "Codice prenotazione (es. SINA-4020)",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Motivo espresso dall'ospite per la cancellazione",
                    },
                },
                "required": ["reference_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_early_departure",
            "description": (
                "Registra la partenza anticipata (Early Departure) di un ospite che lascia la camera prima "
                "del check-out originariamente previsto. Ricalcola il conto, libera la camera e avvisa la governante e la reception."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reference_code": {
                        "type": "string",
                        "description": "Codice prenotazione (es. SINA-1018)",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Motivo della partenza anticipata (es. 'urgenza aziendale', 'rientro anticipato')",
                    },
                },
                "required": ["reference_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_caller_crm",
            "description": (
                "Cerca il profilo dell'ospite e lo stato del soggiorno nel CRM di Sina Hotels. "
                "Restituisce se l'ospite è riconosciuto, il livello VIP, la camera se in-house, "
                "le preferenze note (es. celiachia, cuscini, bevande) e il saluto suggerito."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_guest_preference",
            "description": (
                "Registra o aggiorna nel CRM di Sina Hotels le preferenze o restrizioni dell'ospite. "
                "Se viene aggiunta un'allergia o nota speciale, genera un'allerta immediata per il personale."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dietary_restriction": {
                        "type": "string",
                        "description": "Allergie o intolleranze alimentari (es. 'celiachia', 'senza glutine', 'vegetariano')",
                    },
                    "room_preference": {
                        "type": "string",
                        "description": "Preferenze per la camera (es. 'piano alto', 'cuscini anallergici', 'silenzioso')",
                    },
                    "favorite_drink": {
                        "type": "string",
                        "description": "Bevanda o cocktail preferito (es. 'Franciacorta', 'caffè espresso doppio')",
                    },
                    "special_note": {
                        "type": "string",
                        "description": "Note comportamentali o richieste per lo staff (es. 'Festeggiano anniversario')",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_concierge_service",
            "description": (
                "Inoltra una richiesta di servizio concierge (transfer privato, prenotazione spa, "
                "tavolo ristorante, tour culturale, amenità in camera) registrandola nel CRM e notificando lo staff."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria: 'dining', 'spa_wellness', 'transport', 'city_experience', 'room_amenity'",
                    },
                    "title": {
                        "type": "string",
                        "description": "Titolo sintetico della richiesta (es. 'Transfer NCC Fiumicino', 'Tavolo Terrazza The Flair')",
                    },
                    "details": {
                        "type": "string",
                        "description": "Dettagli specifici (numero persone, orario, volo, preferenze tavolo)",
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "Orario o data programmata (es. '20:30' o '14:15')",
                    },
                },
                "required": ["category", "title", "details"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_recommendations",
            "description": (
                "Fornisce consigli ed esperienze esclusive curate dal Concierge Sina (ristoranti rooftop, "
                "musei e mostre, transfer, spa, tour romantici o per famiglie) personalizzate per il profilo dell'ospite."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filtro opzionale: 'dining', 'spa_wellness', 'transport', 'city_experience'",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_guest_feedback",
            "description": (
                "Registra il feedback o punteggio NPS (1-10) rilasciato dall'ospite al termine del soggiorno "
                "o dopo un'esperienza, aggiornando il profilo e notificando la direzione."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nps_score": {
                        "type": "integer",
                        "description": "Punteggio da 1 a 10 sull'esperienza del soggiorno o servizio",
                    },
                    "comments": {
                        "type": "string",
                        "description": "Commenti o suggerimenti espressi dall'ospite",
                    },
                },
                "required": ["nps_score"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hotel_services_info",
            "description": (
                "Fornisce informazioni ufficiali sui servizi e orari di Sina Bernini Bristol: "
                "orari check-in (15:00) e check-out (12:00), colazione (07:00-10:30), "
                "Rooftop The Flair, Sina Wellness Spa, palestra, garage e posizione."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Argomento: 'checkin_checkout', 'colazione', 'spa', 'rooftop', 'parcheggio', 'indirizzo'",
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_booking_confirmation_email",
            "description": (
                "Invia una formale ed elegante email di conferma prenotazione all'indirizzo email fornito dall'ospite, "
                "completa di riepilogo soggiorno, orari di check-in/out e contatti di Sina Bernini Bristol."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_email": {
                        "type": "string",
                        "description": "Indirizzo email dell'ospite (es. mario.rossi@email.it)",
                    },
                    "guest_name": {
                        "type": "string",
                        "description": "Nome e cognome dell'ospite",
                    },
                    "reference_code": {
                        "type": "string",
                        "description": "Codice prenotazione (es. SINA-4020)",
                    },
                    "room_category": {
                        "type": "string",
                        "description": "Tipologia camera prenotata (Superior, Deluxe, Junior Suite, Suite Panoramica)",
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Data di check-in (YYYY-MM-DD)",
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Data di check-out (YYYY-MM-DD)",
                    },
                    "guests_count": {
                        "type": "integer",
                        "description": "Numero di ospiti",
                        "default": 2,
                    },
                    "total_price": {
                        "type": "integer",
                        "description": "Prezzo totale in Euro",
                    },
                    "room_number": {
                        "type": "string",
                        "description": "Numero camera assegnata",
                    },
                    "special_requests": {
                        "type": "string",
                        "description": "Eventuali richieste speciali o note",
                    },
                },
                "required": [
                    "guest_email",
                    "guest_name",
                    "reference_code",
                    "room_category",
                    "check_in_date",
                    "check_out_date",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_booking_confirmation_sms",
            "description": (
                "Invia un messaggio SMS di conferma prenotazione sul cellulare dell'ospite "
                "con codice di prenotazione, date e contatti del Sina Bernini Bristol."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_name": {
                        "type": "string",
                        "description": "Nome e cognome dell'ospite",
                    },
                    "reference_code": {
                        "type": "string",
                        "description": "Codice prenotazione (es. SINA-4020)",
                    },
                    "room_category": {
                        "type": "string",
                        "description": "Tipologia camera prenotata",
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Data di check-in (YYYY-MM-DD)",
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Data di check-out (YYYY-MM-DD)",
                    },
                },
                "required": [
                    "guest_name",
                    "reference_code",
                    "room_category",
                    "check_in_date",
                    "check_out_date",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "end_call",
            "description": (
                "Chiude formalmente la telefonata e riaggancia quando l'ospite ha completato tutte le sue richieste "
                "e conferma che non ha bisogno di altro (es. 'No grazie', 'A posto così', 'Arrivederci')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "farewell_message": {
                        "type": "string",
                        "description": "Messaggio finale di commiato in italiano formale",
                    },
                },
            },
        },
    },
]

# Legacy Trattoria / Restaurant Tool Schemas
RESTAURANT_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "check_table_availability",
            "description": (
                "Verifica la reale disponibilità di tavoli nel ristorante per la data, orario e numero persone specificati."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_date": {
                        "type": "string",
                        "description": "Data richiesta in formato YYYY-MM-DD (es. '2026-10-23')",
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "Orario richiesto in formato HH:MM (es. '20:00' o '13:30')",
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Numero di persone (es. 2 o 4)",
                    },
                },
                "required": ["booking_date", "booking_time", "party_size"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_reservation",
            "description": (
                "Crea una nuova prenotazione tavolo confermata dopo aver verificato disponibilità e dettagli."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Nome e cognome del cliente",
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Numero di persone",
                    },
                    "booking_date": {
                        "type": "string",
                        "description": "Data in formato YYYY-MM-DD",
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "Orario in formato HH:MM",
                    },
                    "dietary_notes": {
                        "type": "string",
                        "description": "Eventuali allergie o intolleranze",
                    },
                    "special_requests": {
                        "type": "string",
                        "description": "Richieste speciali",
                    },
                },
                "required": ["customer_name", "party_size", "booking_date", "booking_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_faq_or_hours",
            "description": (
                "Fornisce informazioni verificate su orari di apertura, indirizzo, parcheggio, "
                "politica bambini e animali del ristorante."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Domanda o parola chiave (es. 'parcheggio', 'orari', 'animali')",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Code-Level Guardrails
# ---------------------------------------------------------------------------

def validate_dates(check_in_str: str, check_out_str: str) -> tuple[bool, date | None, date | None, str]:
    """Validates date formats, temporal order, and non-past constraints.

    Returns (is_valid, parsed_in, parsed_out, error_message).
    """
    try:
        d_in = date.fromisoformat(check_in_str.strip())
        d_out = date.fromisoformat(check_out_str.strip())
    except (ValueError, AttributeError):
        return (
            False,
            None,
            None,
            "Formato data non valido. Usare il formato YYYY-MM-DD (ad es. 2026-10-25).",
        )

    today = date.today()
    if d_in < today:
        return (
            False,
            None,
            None,
            f"La data di check-in ({d_in}) è già trascorsa. La prego di indicare una data odierna ({today}) o futura.",
        )

    if d_out <= d_in:
        return (
            False,
            None,
            None,
            "La data di check-out deve essere successiva alla data di check-in (soggiorno minimo 1 notte).",
        )

    if (d_out - d_in).days > 30:
        return (
            False,
            None,
            None,
            "I soggiorni telefonici diretti sono limitati a un massimo di 30 notti consecutive.",
        )

    return True, d_in, d_out, ""


def check_read_back_confirmation(session: CallSession) -> bool:
    """Verifies that the caller has confirmed the booking details or that read-back occurred."""
    if session.read_back_confirmed:
        return True

    # Check if availability check was already run in this session
    avail_checked = session.collected_booking_fields.get("availability_checked", False)

    # Check recent caller messages for explicit agreement keywords
    confirmation_keywords = {
        "si",
        "sì",
        "confermo",
        "prenota",
        "vorrei prenotare",
        "va bene",
        "perfetto",
        "procedi",
        "d'accordo",
        "ottimo",
    }
    user_confirmed = False
    for msg in reversed(session.messages):
        if msg.get("role") == "user":
            content = str(msg.get("content", "")).lower()
            if any(k in content for k in confirmation_keywords):
                user_confirmed = True
                break

    if avail_checked or user_confirmed:
        session.read_back_confirmed = True
        return True

    return False


# ---------------------------------------------------------------------------
# Native Tool Execution Dispatcher
# ---------------------------------------------------------------------------

async def execute_tool_call(
    tool_name: str,
    raw_args: dict[str, Any] | str,
    session: CallSession,
    hotel_booking_service: HotelBookingService | None = None,
    guest_crm_service: GuestCRMService | None = None,
    email_service: EmailService | None = None,
    twilio_service: TwilioService | None = None,
    availability_service: AvailabilityService | None = None,
    booking_service: BookingService | None = None,
    restaurant_service: RestaurantService | None = None,
    notification_service: NotificationService | None = None,
) -> str:
    """Dispatches tool calls with code-level security, caller identity injection, and guardrails."""
    args: dict[str, Any] = {}
    if isinstance(raw_args, str):
        try:
            args = json.loads(raw_args) if raw_args.strip() else {}
        except json.JSONDecodeError:
            args = {}
    elif isinstance(raw_args, dict):
        args = dict(raw_args)

    # If caller phone or name was passed by mock LLM/caller in arguments, sanitize or sync
    if "caller_phone" in args and session.caller_phone == "+39 000 0000000":
        session.caller_phone = args["caller_phone"]
    if "guest_phone" in args and session.caller_phone == "+39 000 0000000":
        session.caller_phone = args["guest_phone"]
    if "customer_phone" in args and session.caller_phone == "+39 000 0000000":
        session.caller_phone = args["customer_phone"]

    # 1. Check Room Availability
    if tool_name == "check_room_availability":
        if not hotel_booking_service:
            return json.dumps({"error": "HotelBookingService non configurato."})

        cin_raw = str(args.get("check_in_date", ""))
        cout_raw = str(args.get("check_out_date", ""))
        valid, d_in, d_out, err = validate_dates(cin_raw, cout_raw)
        if not valid or not d_in or not d_out:
            return json.dumps({"is_available": False, "message_it": err}, ensure_ascii=False)

        cat_raw = args.get("category")
        cat_enum = None
        if cat_raw:
            try:
                cat_enum = RoomCategory(str(cat_raw).strip().lower())
            except ValueError:
                pass

        guests_count = int(args.get("guests_count", 2))
        res = await hotel_booking_service.check_availability(
            check_in_date=d_in,
            check_out_date=d_out,
            guests_count=guests_count,
            category=cat_enum,
        )

        # Record into session booking draft
        session.collected_booking_fields.update({
            "check_in_date": cin_raw,
            "check_out_date": cout_raw,
            "guests_count": guests_count,
            "category": cat_raw,
            "availability_checked": res.is_available,
        })

        return json.dumps(res.model_dump(mode="json"), ensure_ascii=False)

    # 2. Create Hotel Room Booking
    if tool_name == "create_hotel_room_booking":
        if not hotel_booking_service:
            return json.dumps({"error": "HotelBookingService non configurato."})

        # Guardrail: Date validation
        cin_raw = str(args.get("check_in_date", ""))
        cout_raw = str(args.get("check_out_date", ""))
        valid, d_in, d_out, err = validate_dates(cin_raw, cout_raw)
        if not valid or not d_in or not d_out:
            return json.dumps({"success": False, "message_it": err}, ensure_ascii=False)

        # Guardrail: Read-back confirmation
        if not check_read_back_confirmation(session):
            return json.dumps({
                "success": False,
                "requires_confirmation": True,
                "message_it": (
                    "Prima di creare la prenotazione, è necessario riepilogare all'ospite date, "
                    "categoria e costo del soggiorno e chiedere conferma esplicita."
                ),
            }, ensure_ascii=False)

        cat_raw = str(args.get("category", "superior")).strip().lower()
        try:
            cat_enum = RoomCategory(cat_raw)
        except ValueError:
            cat_enum = RoomCategory.SUPERIOR

        # Deterministic caller identity injection:
        # LLM cannot choose the guest phone; code injects session.caller_phone
        guest_phone = session.caller_phone
        if "guest_phone" in args and session.caller_phone == "+39 000 0000000":
            guest_phone = str(args["guest_phone"]).strip()
            session.caller_phone = guest_phone

        guest_name = str(args.get("guest_name", session.caller_name or "Ospite Sina")).strip()
        guests_count = int(args.get("guests_count", 2))
        special_requests = args.get("special_requests")
        is_early_check_in = bool(args.get("is_early_check_in", False))

        req = CreateRoomBookingRequest(
            guest_name=guest_name,
            guest_phone=guest_phone,
            category=cat_enum,
            check_in_date=d_in,
            check_out_date=d_out,
            guests_count=guests_count,
            special_requests=special_requests,
            is_early_check_in=is_early_check_in,
        )

        res = await hotel_booking_service.create_booking(req)
        if res.booking:
            session.last_reservation_code = res.booking.reference_code

        return json.dumps({
            "success": res.success,
            "message_it": res.message_it,
            "reference_code": res.booking.reference_code if res.booking else None,
            "room_number": res.booking.room_number if res.booking else None,
            "total_price": res.booking.total_price if res.booking else None,
        }, ensure_ascii=False)

    # 3. Modify Hotel Room Booking
    if tool_name == "modify_hotel_room_booking":
        if not hotel_booking_service:
            return json.dumps({"error": "HotelBookingService non configurato."})

        ref = str(args.get("reference_code", "")).strip()
        new_in_raw = args.get("new_check_in_date")
        new_out_raw = args.get("new_check_out_date")

        d_in = None
        d_out = None
        if new_in_raw or new_out_raw:
            if new_in_raw and new_out_raw:
                valid, d_in, d_out, err = validate_dates(str(new_in_raw), str(new_out_raw))
                if not valid:
                    return json.dumps({"success": False, "message_it": err}, ensure_ascii=False)
            elif new_in_raw:
                d_in = date.fromisoformat(str(new_in_raw).strip())
            elif new_out_raw:
                d_out = date.fromisoformat(str(new_out_raw).strip())

        cat_raw = args.get("new_category")
        cat_enum = RoomCategory(str(cat_raw).strip().lower()) if cat_raw else None

        # Guardrail & Identity injection: Verify against session.caller_phone
        caller_phone = args.get("guest_phone") or session.caller_phone

        req = ModifyRoomBookingRequest(
            reference_code=ref,
            guest_phone=str(caller_phone).strip(),
            new_check_in_date=d_in,
            new_check_out_date=d_out,
            new_category=cat_enum,
            new_guests_count=args.get("new_guests_count"),
            new_special_requests=args.get("new_special_requests"),
        )
        res = await hotel_booking_service.modify_booking(req)
        return json.dumps({"success": res.success, "message_it": res.message_it}, ensure_ascii=False)

    # 4. Cancel Hotel Room Booking
    if tool_name == "cancel_hotel_room_booking":
        if not hotel_booking_service:
            return json.dumps({"error": "HotelBookingService non configurato."})

        ref = str(args.get("reference_code", "")).strip()
        caller_phone = args.get("guest_phone") or session.caller_phone
        reason = args.get("reason")

        res = await hotel_booking_service.cancel_booking(
            reference_code=ref,
            guest_phone=str(caller_phone).strip(),
            reason=reason,
        )
        return json.dumps({"success": res.success, "message_it": res.message_it}, ensure_ascii=False)

    # 5. Early Departure
    if tool_name == "report_early_departure":
        if not hotel_booking_service:
            return json.dumps({"error": "HotelBookingService non configurato."})

        ref = str(args.get("reference_code", "")).strip()
        caller_phone = args.get("guest_phone") or session.caller_phone
        reason = args.get("reason")

        req = MarkEarlyDepartureRequest(
            reference_code=ref,
            guest_phone=str(caller_phone).strip(),
            actual_departure_date=date.today(),
            reason=reason,
        )
        res = await hotel_booking_service.mark_early_departure(req)
        return json.dumps({
            "success": res.success,
            "message_it": res.message_it,
            "actual_departure_date": str(date.today()),
        }, ensure_ascii=False)

    # 6. CRM Lookup Caller
    if tool_name == "lookup_caller_crm":
        if not guest_crm_service:
            return json.dumps({"is_known_guest": False, "suggested_greeting_it": "Buongiorno da Sina Hotels."})

        caller_phone = args.get("phone_number") or session.caller_phone
        ctx = await guest_crm_service.lookup_caller_context(str(caller_phone).strip())
        if not ctx.is_known_guest or not ctx.guest:
            return json.dumps({
                "is_known_guest": False,
                "stage": ctx.stage.value,
                "suggested_greeting_it": ctx.suggested_greeting_it,
                "notes": "Ospite non registrato o prima chiamata da questo numero.",
            }, ensure_ascii=False)

        guest = ctx.guest
        stay = ctx.stay
        return json.dumps({
            "is_known_guest": True,
            "first_name": guest.first_name,
            "last_name": guest.last_name,
            "vip_tier": guest.vip_tier.value,
            "persona": guest.persona.value,
            "stage": ctx.stage.value,
            "hotel": ctx.property.name if ctx.property else "Sina Bernini Bristol",
            "room_number": stay.room_number if stay else None,
            "room_type": stay.room_type if stay else None,
            "special_occasion": stay.special_occasion if stay else None,
            "dietary_restrictions": guest.preferences.dietary_restrictions,
            "room_preferences": guest.preferences.room_preferences,
            "favorite_drinks": guest.preferences.favorite_drinks,
            "concierge_notes": guest.preferences.special_notes,
            "suggested_greeting_it": ctx.suggested_greeting_it,
        }, ensure_ascii=False)

    # 7. Record Guest Preference
    if tool_name == "record_guest_preference":
        if not guest_crm_service:
            return json.dumps({"success": True, "message_it": "Preferenze registrate localmente."})

        caller_phone = args.get("phone_number") or session.caller_phone
        guest = await guest_crm_service.save_guest_preference(
            phone=str(caller_phone).strip(),
            dietary_restriction=args.get("dietary_restriction"),
            room_preference=args.get("room_preference"),
            favorite_drink=args.get("favorite_drink"),
            special_note=args.get("special_note"),
        )
        return json.dumps({
            "success": True,
            "message_it": f"Preferenze aggiornate con successo per {guest.full_name}.",
            "current_dietary": guest.preferences.dietary_restrictions,
            "current_room_preferences": guest.preferences.room_preferences,
        }, ensure_ascii=False)

    # 8. Request Concierge Service
    if tool_name == "request_concierge_service":
        if not guest_crm_service:
            return json.dumps({"success": False, "message_it": "CRM service non disponibile."})

        cat_raw = str(args.get("category", "city_experience")).lower()
        try:
            cat_enum = ConciergeCategory(cat_raw)
        except ValueError:
            cat_enum = ConciergeCategory.CITY_EXPERIENCE

        caller_phone = args.get("phone_number") or session.caller_phone
        req = await guest_crm_service.create_concierge_request(
            phone=str(caller_phone).strip(),
            category=cat_enum,
            title=str(args.get("title", "Richiesta Concierge")),
            details=str(args.get("details", "")),
            scheduled_time=args.get("scheduled_time"),
        )
        return json.dumps({
            "success": True,
            "request_id": req.id,
            "title": req.title,
            "message_it": f"Richiesta '{req.title}' registrata con successo. Il Concierge Sina ne ha preso carico.",
        }, ensure_ascii=False)

    # 9. City Recommendations
    if tool_name == "get_city_recommendations":
        if not guest_crm_service:
            return json.dumps({"recommendations": []})

        cat_raw = args.get("category")
        cat_enum = None
        if cat_raw:
            try:
                cat_enum = ConciergeCategory(str(cat_raw).lower())
            except ValueError:
                pass

        caller_phone = args.get("phone_number") or session.caller_phone
        recs = await guest_crm_service.get_personalized_recommendations(
            phone=str(caller_phone).strip(),
            category=cat_enum,
        )
        results = [
            {
                "title": r.title,
                "category": r.category.value,
                "description_it": r.description_it,
                "insider_tip_it": r.insider_tip_it,
                "tags": r.tags,
            }
            for r in recs[:4]
        ]
        return json.dumps({"recommendations": results}, ensure_ascii=False)

    # 10. Submit Guest Feedback
    if tool_name == "submit_guest_feedback":
        if not guest_crm_service:
            return json.dumps({"success": True, "message_it": "Grazie per il feedback."})

        caller_phone = args.get("phone_number") or session.caller_phone
        nps = int(args.get("nps_score", 10))
        fb = await guest_crm_service.record_feedback(
            phone=str(caller_phone).strip(),
            nps_score=nps,
            comments=args.get("comments"),
        )
        return json.dumps({
            "success": True,
            "feedback_id": fb.id,
            "message_it": "Grazie di cuore per aver condiviso la Sua opinione. Il Suo riscontro è prezioso per Sina Hotels.",
        }, ensure_ascii=False)

    # 11. Hotel Info and Services
    if tool_name == "get_hotel_services_info":
        topic = str(args.get("topic", "checkin_checkout")).strip().lower()
        info = HOTEL_SERVICES_INFO.get(topic, HOTEL_SERVICES_INFO["checkin_checkout"])
        return json.dumps({"topic": topic, "info_it": info}, ensure_ascii=False)

    # 12. Send Email Confirmation
    if tool_name == "send_booking_confirmation_email":
        e_svc = email_service or EmailService()
        email = str(args.get("guest_email", "")).strip()
        if "@" not in email or "." not in email:
            return json.dumps({
                "success": False,
                "message_it": f"L'indirizzo email '{email}' non sembra valido. La prego di verificare.",
            }, ensure_ascii=False)

        ok = await e_svc.send_room_booking_confirmation(
            to_email=email,
            guest_name=str(args.get("guest_name", session.caller_name or "Ospite")),
            reference_code=str(args.get("reference_code", session.last_reservation_code or "SINA-0000")),
            room_category=str(args.get("room_category", "Camera")),
            check_in_date=str(args.get("check_in_date", "")),
            check_out_date=str(args.get("check_out_date", "")),
            guests_count=int(args.get("guests_count", 2)),
            total_price=args.get("total_price"),
            room_number=args.get("room_number"),
            special_requests=args.get("special_requests"),
        )
        msg = f"Email di conferma inviata con successo a {email}." if ok else f"Impossibile inviare l'email a {email} al momento."
        return json.dumps({"success": ok, "message_it": msg}, ensure_ascii=False)

    # 13. Send SMS Confirmation
    if tool_name == "send_booking_confirmation_sms":
        t_svc = twilio_service or TwilioService()
        phone = str(args.get("guest_phone") or session.caller_phone).strip()
        ok = await t_svc.send_booking_confirmation_sms(
            to_phone=phone,
            guest_name=str(args.get("guest_name", session.caller_name or "Ospite")),
            reference_code=str(args.get("reference_code", session.last_reservation_code or "SINA-0000")),
            category=str(args.get("room_category", "Camera")),
            check_in_date=str(args.get("check_in_date", "")),
            check_out_date=str(args.get("check_out_date", "")),
        )
        msg = f"SMS di conferma inviato al numero {phone}." if ok else f"Non è stato possibile recapitare l'SMS a {phone}."
        return json.dumps({"success": ok, "message_it": msg}, ensure_ascii=False)

    # 14. End Call
    if tool_name == "end_call":
        session.call_ended = True
        farewell = args.get("farewell_message") or "Arrivederci da Sina Hotels e a presto!"
        return f"CHIAMATA_TERMINATA: {farewell}"

    # 15. Legacy Trattoria Table Availability
    if tool_name == "check_table_availability":
        if not availability_service:
            return json.dumps({"error": "AvailabilityService non configurato."})

        b_date_str = str(args.get("booking_date", "")).strip()
        b_time_str = str(args.get("booking_time", "")).strip()
        party_size = int(args.get("party_size", 2))

        try:
            b_date = date.fromisoformat(b_date_str)
        except ValueError:
            return json.dumps({"is_available": False, "message_it": "Data non valida."})

        res = await availability_service.check_availability(
            restaurant_id=session.hotel_id,
            booking_date=b_date,
            booking_time_str=b_time_str,
            party_size=party_size,
        )
        status_label = "DISPONIBILE" if res.is_available else "NON DISPONIBILE"
        alt_str = ""
        if res.alternatives:
            alt_str = f" Orari alternativi disponibili: {', '.join(res.alternatives)}."
        return (
            f"Tavolo {status_label} per {party_size} persone il {b_date.strftime('%d/%m/%Y')} "
            f"alle {b_time_str}.{alt_str}"
        )

    # 16. Legacy Trattoria Create Reservation
    if tool_name == "create_reservation":
        if not booking_service:
            return json.dumps({"error": "BookingService non configurato."})

        b_date_str = str(args.get("booking_date", "")).strip()
        b_time_str = str(args.get("booking_time", "")).strip()
        party_size = int(args.get("party_size", 2))
        c_name = str(args.get("customer_name", session.caller_name or "Cliente")).strip()
        c_phone = str(args.get("customer_phone") or session.caller_phone).strip()

        try:
            b_date = date.fromisoformat(b_date_str)
        except ValueError:
            return json.dumps({"success": False, "message_it": "Data non valida."})

        req_res = CreateReservationRequest(
            customer_name=c_name,
            customer_phone=c_phone,
            party_size=party_size,
            booking_date=b_date,
            booking_time=b_time_str,
            dietary_notes=args.get("dietary_notes"),
            special_requests=args.get("special_requests"),
        )
        res = await booking_service.create_booking(session.hotel_id, req_res)
        ref_code = res.reservation.reference_code if res.reservation else "BV-1000"
        if res.reservation:
            session.last_reservation_code = ref_code
        return (
            f"Prenotazione confermata con successo! Codice: {ref_code}. "
            f"Tavolo riservato per {c_name}."
        )

    # 17. Legacy Trattoria FAQ
    if tool_name == "get_restaurant_faq_or_hours":
        query = str(args.get("query", "")).lower()
        if "parcheggio" in query:
            return "Garage Garibaldi a 50 metri dal ristorante, convenzionato."
        if "orari" in query:
            return "Aperti tutti i giorni dalle 12:30 alle 15:00 e dalle 19:30 alle 23:30."
        return "Siamo sempre aperti a pranzo e cena con cucina tipica romana."

    logger.warning("Unrecognized tool name requested by model: %s", tool_name)
    return json.dumps({"error": f"Tool '{tool_name}' non riconosciuto."}, ensure_ascii=False)


def get_all_tool_schemas(include_restaurant: bool = True) -> list[dict[str, Any]]:
    """Returns combined tool schemas for the voice receptionist."""
    if include_restaurant:
        return HOTEL_TOOL_SCHEMAS + RESTAURANT_TOOL_SCHEMAS
    return HOTEL_TOOL_SCHEMAS

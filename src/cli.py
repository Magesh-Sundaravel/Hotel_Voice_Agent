import asyncio
from datetime import date, datetime

from src.repositories import (
    get_booking_repository,
    get_guest_crm_repository,
    get_hotel_room_repository,
    get_notification_repository,
    get_restaurant_repository,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.voice.agent import VoiceAgent
from src.voice.session import CallSession


async def run_simulator():
    print("=" * 70)
    print(" 🏨  SIMULATORE VOCALE RICEZIONISTA AI - SINA HOTELS")
    print("     Sina Bernini Bristol — Piazza Barberini, Roma")
    print("=" * 70)
    print("Comandi speciali:")
    print("  /notifiche     - Visualizza le notifiche registrate nel CRM")
    print("  /prenotazioni  - Elenca le prenotazioni camere nel gestionale")
    print("  /chiudi        - Riaggancia manualmente la telefonata")
    print("  /reset         - Termina la telefonata corrente e ne avvia una nuova")
    print("  /esci          - Chiude il simulatore")
    print("-" * 70)

    caller_phone = input(
        "Inserisci numero chiamante (default: +39 333 4567890): "
    ).strip()
    if not caller_phone:
        caller_phone = "+39 333 4567890"

    caller_name = input(
        "Inserisci nome chiamante (opzionale, es. Mario Rossi): "
    ).strip()
    if not caller_name:
        caller_name = None

    print(
        f"\n[SISTEMA] Connessione centralino... Chiamata in arrivo da: {caller_phone} ({caller_name or 'Sconosciuto'})"
    )
    print("[SISTEMA] Inizializzazione VoiceAgent nativo...")

    hotel_room_repo = get_hotel_room_repository()
    notification_repo = get_notification_repository()
    guest_crm_repo = get_guest_crm_repository()
    restaurant_repo = get_restaurant_repository()
    booking_repo = get_booking_repository()

    crm_svc = GuestCRMService(
        crm_repo=guest_crm_repo,
        notification_repo=notification_repo,
        default_hotel_id="sina_bernini_bristol",
    )
    hotel_booking_svc = HotelBookingService(
        room_repo=hotel_room_repo,
        notification_repo=notification_repo,
        guest_crm_service=crm_svc,
        hotel_id="sina_bernini_bristol",
    )
    restaurant_svc = RestaurantService(restaurant_repo)
    availability_svc = AvailabilityService(restaurant_repo, booking_repo)
    booking_svc = BookingService(
        booking_repo=booking_repo,
        availability_service=availability_svc,
        notification_service=NotificationService(notification_repo),
    )

    try:
        agent = VoiceAgent(
            hotel_id="sina_bernini_bristol",
            hotel_name="Sina Bernini Bristol",
            hotel_booking_service=hotel_booking_svc,
            guest_crm_service=crm_svc,
            availability_service=availability_svc,
            booking_service=booking_svc,
            restaurant_service=restaurant_svc,
        )
    except Exception as e:  # noqa: BLE001
        print(f"\n[ERRORE] Impossibile avviare VoiceAgent con Groq: {e}")
        print("Assicurati di impostare GROQ_API_KEY nel file .env!")
        return

    def create_fresh_session():
        cid = f"call_{caller_phone.replace(' ', '')}_{int(datetime.now().timestamp())}"
        clean_phone = caller_phone.replace(" ", "").replace("+", "")
        return CallSession(
            call_id=cid,
            user_id=f"user_{clean_phone}",
            caller_phone=caller_phone,
            caller_name=caller_name,
            hotel_id="sina_bernini_bristol",
            hotel_name="Sina Bernini Bristol",
        )

    session = create_fresh_session()

    print("\n[AI]: ", end="")
    try:
        res = await agent.run_turn(session, "Pronto? Buongiorno.")
        print(res.reply_text)
    except Exception as e:  # noqa: BLE001
        print(f"Errore durante l'elaborazione: {e}")
        return

    # Conversation loop
    while True:
        try:
            user_text = input("\n[TU / CHIAMANTE]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nChiamata terminata.")
            break

        if not user_text:
            continue

        if user_text.lower() in ["/esci", "esci", "exit", "quit"]:
            print("\nArrivederci!")
            break

        if user_text.lower() in ["/chiudi", "riattacca", "/hangup"]:
            print("\n📴 [HAI RIAGGANCIATO IL RICEVITORE]")
            choice = (
                input("\nVuoi effettuare un'altra chiamata? (s/n, default 's'): ")
                .strip()
                .lower()
            )
            if choice == "n":
                print("\nArrivederci!")
                break
            session = create_fresh_session()
            res = await agent.run_turn(session, "Pronto? Buongiorno.")
            print(f"\n[AI]: {res.reply_text}")
            continue

        if user_text.lower() == "/notifiche":
            repo = get_notification_repository()
            notifs = await repo.get_notifications("sina_bernini_bristol")
            print("\n--- NOTIFICHE CRM HOTEL SINA BERNINI BRISTOL ---")
            if not notifs:
                print("Nessuna notifica presente.")
            for n in notifs:
                status = "🔴 Non letta" if not n.is_read else "🟢 Letta"
                print(
                    f"[{n.created_at.strftime('%H:%M:%S')}] {status} [{n.type.value.upper()}] {n.title}"
                )
                print(f"    Messaggio: {n.message}")
            print("------------------------------------")
            continue

        if user_text.lower() == "/prenotazioni":
            repo = get_booking_repository()
            bookings = await repo.get_reservations_for_date(
                "sina_bernini_bristol", date.today(), status=None
            )
            print(
                f"\n--- PRENOTAZIONI CONFERMATE OGGI ({date.today().strftime('%d/%m/%Y')}) ---"
            )
            if not bookings:
                print("Nessuna prenotazione trovata per oggi.")
            for b in bookings:
                print(
                    f"[{b.reference_code}] {b.booking_time} - {b.customer_name} ({b.party_size} persone) Tel: {b.customer_phone} [Stato: {b.status.value}]"
                )
                if b.dietary_notes:
                    print(f"    Note dietetiche: {b.dietary_notes}")
            print(
                "-------------------------------------------------------------------"
            )
            continue

        if user_text.lower() == "/reset":
            print("\n[SISTEMA] Reset conversazione e nuova chiamata.")
            session = create_fresh_session()
            res = await agent.run_turn(session, "Pronto? Buongiorno.")
            print(f"\n[AI]: {res.reply_text}")
            continue

        try:
            res = await agent.run_turn(session, user_text)
            print(f"\n[AI]: {res.reply_text}")

            if res.call_ended:
                print("\n" + "=" * 50)
                print("📴  [TELEFONATA CONCLUSA - RICEVITORE RIAGGANCIATO]")
                print("=" * 50)
                choice = (
                    input(
                        "\nVuoi simulare una nuova telefonata? (s/n, default 's'): "
                    )
                    .strip()
                    .lower()
                )
                if choice == "n":
                    print("\nArrivederci!")
                    break
                print("\n[SISTEMA] Nuova telefonata in arrivo...")
                session = create_fresh_session()
                res = await agent.run_turn(session, "Pronto? Buongiorno.")
                print(f"\n[AI]: {res.reply_text}")

        except Exception as e:  # noqa: BLE001
            print(f"\n[ERRORE AGENTE]: {e}")


def main():
    asyncio.run(run_simulator())


if __name__ == "__main__":
    main()

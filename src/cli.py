import asyncio
from datetime import date, datetime

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agent.checkpointer import get_checkpointer
from src.agent.graph import create_agent_graph
from src.agent.prompts import format_date_italian
from src.agent.state import AgentState
from src.config import settings
from src.repositories import get_booking_repository, get_notification_repository


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
    print("[SISTEMA] Inizializzazione agente LangGraph e checkpointer...")

    async with get_checkpointer() as checkpointer:
        try:
            agent = create_agent_graph(
                hotel_id="sina_bernini_bristol",
                hotel_name="Sina Bernini Bristol",
                checkpointer=checkpointer,
            )
        except Exception as e:  # noqa: BLE001
            print(f"\n[ERRORE] Impossibile avviare l'agente con Groq: {e}")
            print("Assicurati di impostare GROQ_API_KEY nel file .env!")
            return

        thread_id = (
            f"call_{caller_phone.replace(' ', '')}_{int(datetime.now().timestamp())}"
        )
        config = {"configurable": {"thread_id": thread_id}}
        current_date = format_date_italian(date.today())

        # Initial greeting trigger
        initial_trigger = HumanMessage(content="Pronto? Buongiorno.")
        state: AgentState = {
            "messages": [initial_trigger],
            "hotel_id": "sina_bernini_bristol",
            "hotel_name": "Sina Bernini Bristol",
            "caller_phone": caller_phone,
            "caller_name": caller_name,
            "current_date": current_date,
        }

        print("\n[AI]: ", end="")
        try:
            result = await agent.ainvoke(state, config=config)
            last_ai = [
                m for m in result["messages"] if isinstance(m, AIMessage) and m.content
            ][-1]
            print(last_ai.content)
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
                # Start fresh call
                thread_id = f"call_{caller_phone.replace(' ', '')}_{int(datetime.now().timestamp())}"
                config = {"configurable": {"thread_id": thread_id}}
                state["messages"] = [HumanMessage(content="Pronto? Buongiorno.")]
                result = await agent.ainvoke(state, config=config)
                last_ai = [
                    m
                    for m in result["messages"]
                    if isinstance(m, AIMessage) and m.content
                ][-1]
                print(f"\n[AI]: {last_ai.content}")
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
                thread_id = f"call_{caller_phone.replace(' ', '')}_{int(datetime.now().timestamp())}"
                config = {"configurable": {"thread_id": thread_id}}
                state["messages"] = [HumanMessage(content="Pronto? Buongiorno.")]
                result = await agent.ainvoke(state, config=config)
                last_ai = [
                    m
                    for m in result["messages"]
                    if isinstance(m, AIMessage) and m.content
                ][-1]
                print(f"\n[AI]: {last_ai.content}")
                continue

            turn_input = {"messages": [HumanMessage(content=user_text)]}

            try:
                result = await agent.ainvoke(turn_input, config=config)
                new_messages = result["messages"]

                # Check if end_call was called
                call_ended = False
                for m in new_messages:
                    if isinstance(m, ToolMessage) and m.name == "end_call":
                        call_ended = True

                last_ai = [
                    m for m in new_messages if isinstance(m, AIMessage) and m.content
                ][-1]
                print(f"\n[AI]: {last_ai.content}")

                if call_ended:
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
                    # Reset for new call
                    print("\n[SISTEMA] Nuova telefonata in arrivo...")
                    thread_id = f"call_{caller_phone.replace(' ', '')}_{int(datetime.now().timestamp())}"
                    config = {"configurable": {"thread_id": thread_id}}
                    state["messages"] = [HumanMessage(content="Pronto? Buongiorno.")]
                    result = await agent.ainvoke(state, config=config)
                    last_ai = [
                        m
                        for m in result["messages"]
                        if isinstance(m, AIMessage) and m.content
                    ][-1]
                    print(f"\n[AI]: {last_ai.content}")

            except Exception as e:  # noqa: BLE001
                print(f"\n[ERRORE AGENTE]: {e}")


def main():
    asyncio.run(run_simulator())


if __name__ == "__main__":
    main()

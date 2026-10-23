from datetime import date, timedelta

from src.models.crm import (
    CityRecommendationItem,
    ConciergeCategory,
    GuestPreferences,
    GuestProfile,
    HotelProperty,
    HotelStay,
    StayStage,
    TravelPersona,
    VIPTier,
)

# Reference dates based on current day
TODAY = date.today()

# ---------------------------------------------------------------------------
# SINA HOTELS PROPERTIES
# ---------------------------------------------------------------------------
SINA_BERNINI_BRISTOL = HotelProperty(
    id="sina_bernini_bristol",
    name="Sina Bernini Bristol, Autograph Collection",
    city="Roma",
    address="Piazza Barberini 23, 00187 Roma",
    phone_number="+39 06 4883051",
    amenities=[
        "Rooftop Restaurant 'The Flair' (alta cucina con vista panoramica a 360° su Roma)",
        "Sina Wellness & Spa (sauna, bagno turco, idromassaggio, massaggi di coppia)",
        "Bar del Bristol (terrazza cocktail e aperitivi d'autore)",
        "Fitness Suite Technogym panoramica",
        "Conciergerie Clefs d'Or (transfer aeroporto privati NCC, tour guidati)",
    ],
    schedules={
        "colazione": "07:00 - 10:30 (Salone Bernini o servizio in camera)",
        "ristorante_the_flair": "19:30 - 23:00 (Cena gourmet panoramica)",
        "bar_del_bristol": "10:30 - 00:30",
        "spa_wellness": "10:00 - 20:00 (su appuntamento)",
        "check_in": "dalle ore 15:00",
        "check_out": "entro le ore 12:00 (Late check-out su richiesta)",
    },
)

SAMPLE_PROPERTIES = {
    SINA_BERNINI_BRISTOL.id: SINA_BERNINI_BRISTOL,
}

# ---------------------------------------------------------------------------
# SAMPLE GUESTS & STAYS (Representing Pre-Stay, In-House, Post-Stay)
# ---------------------------------------------------------------------------

# GUEST 1: IN-HOUSE - Romantic Couple celebrating 10th Anniversary
GUEST_COUPLE = GuestProfile(
    id="guest_rossi_01",
    phone_number="+393331112233",
    email="marco.rossi@example.com",
    title="Signor",
    first_name="Marco",
    last_name="Rossi",
    preferred_language="it",
    vip_tier=VIPTier.GOLD,
    persona=TravelPersona.ROMANTIC_COUPLE,
    preferences=GuestPreferences(
        dietary_restrictions=["celiachia rigorosa (la Signora Giulia è celiaca)"],
        room_preferences=["piano alto", "cuscini anallergici", "ambiente silenzioso"],
        favorite_drinks=["Franciacorta Brut", "tisana ai frutti di bosco"],
        special_notes="Festeggiano il 10° anniversario di nozze. Gradito tavolo appartato vista tramonto.",
    ),
    total_stays=3,
    loyalty_points=4200,
)

STAY_COUPLE_IN_HOUSE = HotelStay(
    id="stay_bb_402",
    guest_id=GUEST_COUPLE.id,
    hotel_id=SINA_BERNINI_BRISTOL.id,
    room_number="402",
    room_type="Panoramic Suite Barberini",
    check_in_date=TODAY - timedelta(days=1),
    check_out_date=TODAY + timedelta(days=2),
    stage=StayStage.IN_HOUSE,
    party_size=2,
    special_occasion="10° Anniversario di Nozze",
    internal_notes="In-house. Bottiglia di Franciacorta di benvenuto già omaggiata in camera 402.",
)

# GUEST 2: PRE-STAY - Business Solo Traveler with VIP status
GUEST_BUSINESS = GuestProfile(
    id="guest_moretti_02",
    phone_number="+393359988776",
    email="andrea.moretti@corporate.it",
    title="Signor",
    first_name="Andrea",
    last_name="Moretti",
    preferred_language="it",
    vip_tier=VIPTier.SINA_PRIVILEGE_VIP,
    persona=TravelPersona.BUSINESS_SOLO,
    preferences=GuestPreferences(
        dietary_restrictions=["nessuna allergia", "preferenza colazione proteica"],
        room_preferences=["scrivania da lavoro", "ferro da stiro", "Wi-Fi premium"],
        favorite_drinks=["Caffè espresso doppio ristretto", "Acqua minerale frizzante"],
        special_notes="Ospite frequente Sina Privilege. Richiede sempre transfer NCC Fiumicino e massima puntualità.",
    ),
    total_stays=14,
    loyalty_points=21500,
)

STAY_BUSINESS_PRE = HotelStay(
    id="stay_bb_pre_881",
    guest_id=GUEST_BUSINESS.id,
    hotel_id=SINA_BERNINI_BRISTOL.id,
    room_number=None,
    room_type="Executive Deluxe King",
    check_in_date=TODAY + timedelta(days=1),
    check_out_date=TODAY + timedelta(days=3),
    stage=StayStage.PRE_STAY,
    party_size=1,
    special_occasion="Conferenza Finanziaria Internazionale",
    internal_notes="Arrivo previsto domani alle 14:00. Richiesto check-in prioritario.",
)

# GUEST 3: POST-STAY - Family Leisure Traveler for Feedback & Loyalty
GUEST_FAMILY = GuestProfile(
    id="guest_bianchi_03",
    phone_number="+393405544332",
    email="elena.bianchi@gmail.com",
    title="Signora",
    first_name="Elena",
    last_name="Bianchi",
    preferred_language="it",
    vip_tier=VIPTier.SILVER,
    persona=TravelPersona.FAMILY_LEISURE,
    preferences=GuestPreferences(
        dietary_restrictions=["vegetariano (Elena)", "menu bimbi semplice per i due figli"],
        room_preferences=["suite con zona giorno separata o camere comunicanti"],
        favorite_drinks=["Cappuccino con latte di mandorla", "spremuta d'arancia fresca"],
        special_notes="Viaggia con il marito Luca e i figli Leo (8 anni) e Sofia (11 anni).",
    ),
    total_stays=2,
    loyalty_points=2400,
)

STAY_FAMILY_POST = HotelStay(
    id="stay_bb_post_305",
    guest_id=GUEST_FAMILY.id,
    hotel_id=SINA_BERNINI_BRISTOL.id,
    room_number="305",
    room_type="Family Deluxe Suite",
    check_in_date=TODAY - timedelta(days=5),
    check_out_date=TODAY - timedelta(days=1),
    stage=StayStage.POST_STAY,
    party_size=4,
    special_occasion="Vacanza in famiglia a Roma",
    internal_notes="Partiti ieri mattina. Esperienza ottima, ha espresso interesse per Sina Villa Medici a Firenze.",
)

SAMPLE_GUESTS = {
    GUEST_COUPLE.phone_number: GUEST_COUPLE,
    GUEST_BUSINESS.phone_number: GUEST_BUSINESS,
    GUEST_FAMILY.phone_number: GUEST_FAMILY,
}

SAMPLE_STAYS = {
    STAY_COUPLE_IN_HOUSE.guest_id: STAY_COUPLE_IN_HOUSE,
    STAY_BUSINESS_PRE.guest_id: STAY_BUSINESS_PRE,
    STAY_FAMILY_POST.guest_id: STAY_FAMILY_POST,
}

# ---------------------------------------------------------------------------
# SINA CONCIERGE CURATED CITY EXPERIENCES & RECOMMENDATIONS
# ---------------------------------------------------------------------------
SAMPLE_RECOMMENDATIONS: list[CityRecommendationItem] = [
    CityRecommendationItem(
        id="rec_the_flair",
        hotel_id=SINA_BERNINI_BRISTOL.id,
        category=ConciergeCategory.DINING,
        title="Cena Gourmet sul Rooftop 'The Flair'",
        description_it="Cena a lume di candela al nostro rooftop restaurant all'ultimo piano dell'hotel, con vista mozzafiato su Roma illuminata e Piazza Barberini.",
        description_en="Candlelight gourmet dinner at our rooftop restaurant atop the hotel, with breathtaking 360-degree views over illuminated Rome.",
        tags=["romantico", "rooftop", "vista", "anniversario", "alta cucina", "in-house"],
        recommended_for=[TravelPersona.ROMANTIC_COUPLE, TravelPersona.GENERAL_LEISURE],
        insider_tip_it="Prenotiamo per voi il tavolo ad angolo verso il tramonto con servizio dedicato e opzioni 100% gluten-free.",
    ),
    CityRecommendationItem(
        id="rec_couple_spa_ritual",
        hotel_id=SINA_BERNINI_BRISTOL.id,
        category=ConciergeCategory.SPA_WELLNESS,
        title="Rituale di Coppia 'Sina Sensations'",
        description_it="Percorso benessere esclusivo con bagno turco aromaterapico e massaggio rilassante di coppia con oli essenziali d'agrumi.",
        description_en="Exclusive wellness path with aromatherapeutic Turkish bath and couple's relaxing massage with Mediterranean citrus oils.",
        tags=["spa", "coppia", "relax", "benessere", "massaggi"],
        recommended_for=[TravelPersona.ROMANTIC_COUPLE, TravelPersona.WELLNESS_SEEKER],
        insider_tip_it="Consigliato nel tardo pomeriggio prima dell'aperitivo sulla terrazza.",
    ),
    CityRecommendationItem(
        id="rec_galleria_borghese_vip",
        hotel_id=SINA_BERNINI_BRISTOL.id,
        category=ConciergeCategory.CITY_EXPERIENCE,
        title="Visita Esclusiva alla Galleria Borghese con Guida d'Arte",
        description_it="Accesso riservato salta-fila ai capolavori scultorei del Bernini (Apollo e Dafne, Ratto di Proserpina) a pochi minuti a piedi dall'hotel.",
        description_en="Skip-the-line VIP access to Gian Lorenzo Bernini's masterpieces at Galleria Borghese, just a scenic stroll from the hotel.",
        tags=["bernini", "arte", "cultura", "museo", "salta la fila"],
        recommended_for=[TravelPersona.CULTURE_EXPLORER, TravelPersona.ROMANTIC_COUPLE],
        insider_tip_it="Il nostro concierge riserva i biglietti VIP esclusivi anche quando il museo risulta sold out al pubblico.",
    ),
    CityRecommendationItem(
        id="rec_fco_executive_transfer",
        hotel_id=SINA_BERNINI_BRISTOL.id,
        category=ConciergeCategory.TRANSPORT,
        title="Transfer Privato NCC Mercedes Classe E (Aeroporto FCO)",
        description_it="Autista privato NCC con cartello di benvenuto direttamente al terminal degli arrivi di Roma Fiumicino o Ciampino fino all'hotel.",
        description_en="Private chauffeur service in a Mercedes E-Class directly from Rome Fiumicino (FCO) arrivals gate to the hotel.",
        tags=["transfer", "aeroporto", "fiumicino", "fco", "ncc", "autista", "puntualità"],
        recommended_for=[TravelPersona.BUSINESS_SOLO, TravelPersona.GENERAL_LEISURE],
        insider_tip_it="Autista puntuale con monitoraggio del volo in tempo reale; tariffa convenzionata fissa.",
    ),
    CityRecommendationItem(
        id="rec_business_express_lunch",
        hotel_id=SINA_BERNINI_BRISTOL.id,
        category=ConciergeCategory.DINING,
        title="Pranzo Riservato al Lounge Bar del Bristol",
        description_it="Ambiente riservato ed elegante ideale per colloqui o lavoro, con menu leggero e servizio veloce in 40 minuti.",
        description_en="Private and elegant lounge environment ideal for meetings, with a curated express light lunch served in under 40 minutes.",
        tags=["business lunch", "veloce", "riservato", "lavoro", "wi-fi"],
        recommended_for=[TravelPersona.BUSINESS_SOLO],
        insider_tip_it="Tavolo appartato con prese di corrente e connessione Wi-Fi ultra veloce garantita.",
    ),
    CityRecommendationItem(
        id="rec_family_gladiator_tour",
        hotel_id=SINA_BERNINI_BRISTOL.id,
        category=ConciergeCategory.CITY_EXPERIENCE,
        title="Tour Guidato per Famiglie al Colosseo e Fori Romani",
        description_it="Esperienza interattiva con guida specializzata per ragazzi e bambini per rivivere i fasti dell'Antica Roma senza code estenuanti.",
        description_en="Interactive family-friendly tour of the Colosseum and Roman Forum tailored for children with engaging storytelling.",
        tags=["famiglia", "bambini", "colosseo", "roma antica", "didattico"],
        recommended_for=[TravelPersona.FAMILY_LEISURE],
        insider_tip_it="Include mappa illustrata per i bambini e sosta gelato artigianale consigliata.",
    ),
]

-- ==============================================================================
-- 002_hotel_crm.sql — SINA HOTELS (SINA BERNINI BRISTOL) HOTEL & CRM MIGRATION
-- ==============================================================================

-- 1. HOTELS / PROPERTIES
CREATE TABLE IF NOT EXISTS public.hotels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    address TEXT NOT NULL,
    timezone TEXT DEFAULT 'Europe/Rome',
    amenities TEXT[] DEFAULT '{}',
    schedules JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. HOTEL ROOMS INVENTORY
CREATE TABLE IF NOT EXISTS public.hotel_rooms (
    room_number TEXT PRIMARY KEY,
    hotel_id TEXT REFERENCES public.hotels(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- 'superior', 'deluxe', 'junior_suite', 'panoramic_suite'
    name TEXT NOT NULL,
    price_per_night NUMERIC(10,2) NOT NULL,
    max_guests INT DEFAULT 2,
    floor INT DEFAULT 1,
    features TEXT[] DEFAULT '{}',
    is_clean BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. ROOM BOOKINGS
CREATE TABLE IF NOT EXISTS public.room_bookings (
    id TEXT PRIMARY KEY,
    reference_code TEXT UNIQUE NOT NULL, -- Es. SINA-4020
    hotel_id TEXT REFERENCES public.hotels(id) ON DELETE CASCADE,
    guest_name TEXT NOT NULL,
    guest_phone TEXT NOT NULL,
    guest_email TEXT,
    room_number TEXT REFERENCES public.hotel_rooms(room_number),
    room_category TEXT NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    nights INT NOT NULL,
    guests_count INT DEFAULT 2,
    price_per_night NUMERIC(10,2) NOT NULL,
    total_price NUMERIC(10,2) NOT NULL,
    special_requests TEXT,
    is_early_check_in BOOLEAN DEFAULT FALSE,
    is_early_departure BOOLEAN DEFAULT FALSE,
    early_departure_reason TEXT,
    actual_departure_date DATE,
    status TEXT DEFAULT 'confirmed', -- 'confirmed', 'checked_in', 'checked_out', 'early_departure', 'cancelled'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_room_bookings_dates ON public.room_bookings(hotel_id, check_in_date, check_out_date);
CREATE INDEX IF NOT EXISTS idx_room_bookings_phone ON public.room_bookings(guest_phone);
CREATE INDEX IF NOT EXISTS idx_room_bookings_status ON public.room_bookings(status);

-- 4. GUEST CRM 360 PROFILES
CREATE TABLE IF NOT EXISTS public.crm_guests (
    id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE NOT NULL,
    email TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    preferred_language TEXT DEFAULT 'it',
    vip_tier TEXT DEFAULT 'standard', -- 'standard', 'silver', 'gold', 'sina_privilege_vip'
    persona TEXT DEFAULT 'general_leisure',
    dietary_restrictions TEXT[] DEFAULT '{}',
    room_preferences TEXT[] DEFAULT '{}',
    favorite_drinks TEXT[] DEFAULT '{}',
    special_notes TEXT,
    total_stays INT DEFAULT 1,
    loyalty_points INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crm_guests_phone ON public.crm_guests(phone_number);

-- 5. HOTEL STAYS
CREATE TABLE IF NOT EXISTS public.hotel_stays (
    id TEXT PRIMARY KEY,
    guest_id TEXT REFERENCES public.crm_guests(id) ON DELETE CASCADE,
    hotel_id TEXT REFERENCES public.hotels(id) ON DELETE CASCADE,
    room_number TEXT,
    room_type TEXT NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    stage TEXT DEFAULT 'pre_stay', -- 'pre_stay', 'in_house', 'post_stay', 'non_resident'
    party_size INT DEFAULT 2,
    special_occasion TEXT,
    internal_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hotel_stays_guest ON public.hotel_stays(guest_id);

-- 6. CONCIERGE REQUESTS
CREATE TABLE IF NOT EXISTS public.concierge_requests (
    id TEXT PRIMARY KEY,
    stay_id TEXT,
    guest_id TEXT REFERENCES public.crm_guests(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    request_details TEXT NOT NULL,
    status TEXT DEFAULT 'confirmed',
    scheduled_time TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_concierge_requests_guest ON public.concierge_requests(guest_id);

-- 7. GUEST FEEDBACK
CREATE TABLE IF NOT EXISTS public.guest_feedback (
    id TEXT PRIMARY KEY,
    guest_id TEXT REFERENCES public.crm_guests(id) ON DELETE CASCADE,
    stay_id TEXT,
    nps_score INT NOT NULL,
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. CITY RECOMMENDATIONS
CREATE TABLE IF NOT EXISTS public.city_recommendations (
    id TEXT PRIMARY KEY,
    hotel_id TEXT REFERENCES public.hotels(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description_it TEXT NOT NULL,
    description_en TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    recommended_for TEXT[] DEFAULT '{}',
    insider_tip_it TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. HOTEL OFFICIAL FAQS
CREATE TABLE IF NOT EXISTS public.hotel_faqs (
    id TEXT PRIMARY KEY,
    hotel_id TEXT REFERENCES public.hotels(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    question_it TEXT NOT NULL,
    answer_it TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. COMPATIBILITY VIEWS
CREATE OR REPLACE VIEW public.hotel_bookings AS SELECT * FROM public.room_bookings;
CREATE OR REPLACE VIEW public.guests AS SELECT * FROM public.crm_guests;

-- ==============================================================================
-- SEED DATA: SINA BERNINI BRISTOL (ROMA)
-- ==============================================================================

-- 1. Property
INSERT INTO public.hotels (id, name, city, phone_number, address, timezone, amenities, schedules)
VALUES (
    'sina_bernini_bristol',
    'Sina Bernini Bristol, Autograph Collection',
    'Roma',
    '+39 06 4883051',
    'Piazza Barberini 23, 00187 Roma',
    'Europe/Rome',
    ARRAY['Rooftop Restaurant The Flair', 'Sina Wellness & Spa', 'Bar del Bristol', 'Car Valet Privato', 'Fitness Suite'],
    '{
        "check_in": "dalle ore 15:00",
        "check_out": "entro le ore 12:00",
        "colazione": "07:00 - 10:30",
        "rooftop_the_flair": "19:30 - 23:30",
        "spa": "10:00 - 20:00"
    }'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- 2. 9 Rooms Inventory
INSERT INTO public.hotel_rooms (room_number, hotel_id, category, name, price_per_night, max_guests, floor, features)
VALUES
    ('101', 'sina_bernini_bristol', 'superior', 'Camera Superior 101', 250.00, 2, 1, ARRAY['Letto King', 'Bagno in marmo', 'Affaccio silenzioso']),
    ('102', 'sina_bernini_bristol', 'superior', 'Camera Superior 102', 250.00, 2, 1, ARRAY['Letto Queen', 'Bagno in marmo', 'Doccia a pioggia']),
    ('201', 'sina_bernini_bristol', 'deluxe', 'Camera Deluxe 201 (Vista Piazza)', 350.00, 2, 2, ARRAY['Vista Piazza Barberini', 'Salottino', 'Vasca da bagno']),
    ('202', 'sina_bernini_bristol', 'deluxe', 'Camera Deluxe 202 (Vista Piazza)', 350.00, 2, 2, ARRAY['Vista Fontana del Tritone', 'Letto King', 'Caffè Illy']),
    ('203', 'sina_bernini_bristol', 'deluxe', 'Camera Deluxe 203', 350.00, 2, 2, ARRAY['Letto King', 'Scrivania lavoro ergonomica', 'Cabina armadio']),
    ('301', 'sina_bernini_bristol', 'junior_suite', 'Junior Suite 301 con Balcone', 480.00, 3, 3, ARRAY['Balcone privato', 'Divano letto', 'Doccia cromoterapica']),
    ('302', 'sina_bernini_bristol', 'junior_suite', 'Junior Suite 302 con Balcone', 480.00, 3, 3, ARRAY['Balcone Via Veneto', 'Salotto separato', 'Idromassaggio']),
    ('401', 'sina_bernini_bristol', 'panoramic_suite', 'Suite Panoramica 401', 750.00, 4, 4, ARRAY['Attico privato', 'Terrazza 40mq', 'Vista 360° Roma', 'Maggiordomo']),
    ('402', 'sina_bernini_bristol', 'panoramic_suite', 'Suite Panoramica Barberini 402', 750.00, 4, 4, ARRAY['Suite attico lusso', 'Jacuzzi panoramica', 'Franciacorta omaggio'])
ON CONFLICT (room_number) DO NOTHING;

-- 3. Sample Guest Profiles
INSERT INTO public.crm_guests (id, phone_number, first_name, last_name, vip_tier, persona, dietary_restrictions, room_preferences, favorite_drinks, special_notes, total_stays, loyalty_points)
VALUES
    (
        'guest_rossi_01',
        '+393331112233',
        'Marco',
        'Rossi',
        'gold',
        'romantic_couple',
        ARRAY['celiachia rigorosa (la Signora Giulia è celiaca)'],
        ARRAY['piano alto', 'cuscini anallergici', 'ambiente silenzioso'],
        ARRAY['Franciacorta Brut', 'tisana ai frutti di bosco'],
        'Festeggiano il 10° anniversario di nozze. Gradito tavolo appartato vista tramonto.',
        3,
        4200
    ),
    (
        'guest_moretti_02',
        '+393359988776',
        'Andrea',
        'Moretti',
        'sina_privilege_vip',
        'business_solo',
        ARRAY['nessuna allergia', 'colazione proteica'],
        ARRAY['scrivania da lavoro', 'ferro da stiro', 'Wi-Fi premium'],
        ARRAY['Caffè espresso doppio ristretto'],
        'Membro Sina Privilege VIP. Richiede sempre transfer NCC Fiumicino e massima puntualità.',
        14,
        21500
    ),
    (
        'guest_ferri_03',
        '+393471234567',
        'Roberto',
        'Ferri',
        'standard',
        'business_solo',
        ARRAY[]::text[],
        ARRAY['camera silenziosa'],
        ARRAY[]::text[],
        'Partenza anticipata effettuata per urgenza lavorativa a Milano.',
        1,
        0
    ),
    (
        'guest_bianchi_03',
        '+393405544332',
        'Elena',
        'Bianchi',
        'silver',
        'family_leisure',
        ARRAY['vegetariano (Elena)', 'menu bimbi semplice per i due figli'],
        ARRAY['suite con zona giorno separata o camere comunicanti'],
        ARRAY['Cappuccino con latte di mandorla', 'spremuta d''arancia fresca'],
        'Viaggia con il marito Luca e i figli Leo (8 anni) e Sofia (11 anni).',
        2,
        2400
    )
ON CONFLICT (phone_number) DO NOTHING;

-- 4. Sample Stays
INSERT INTO public.hotel_stays (id, guest_id, hotel_id, room_number, room_type, check_in_date, check_out_date, stage, party_size, special_occasion, internal_notes)
VALUES
    (
        'stay_bb_402',
        'guest_rossi_01',
        'sina_bernini_bristol',
        '402',
        'Panoramic Suite Barberini',
        CURRENT_DATE - INTERVAL '1 day',
        CURRENT_DATE + INTERVAL '2 days',
        'in_house',
        2,
        '10° Anniversario di Nozze',
        'In-house. Bottiglia di Franciacorta di benvenuto già omaggiata in camera 402.'
    ),
    (
        'stay_bb_pre_881',
        'guest_moretti_02',
        'sina_bernini_bristol',
        NULL,
        'Executive Deluxe King',
        CURRENT_DATE + INTERVAL '1 day',
        CURRENT_DATE + INTERVAL '3 days',
        'pre_stay',
        1,
        'Conferenza Finanziaria Internazionale',
        'Arrivo previsto domani alle 14:00. Richiesto check-in prioritario.'
    ),
    (
        'stay_bb_post_305',
        'guest_bianchi_03',
        'sina_bernini_bristol',
        '305',
        'Family Deluxe Suite',
        CURRENT_DATE - INTERVAL '5 days',
        CURRENT_DATE - INTERVAL '1 day',
        'post_stay',
        4,
        'Vacanza in famiglia a Roma',
        'Partiti ieri mattina. Esperienza ottima, ha espresso interesse per Sina Villa Medici a Firenze.'
    )
ON CONFLICT (id) DO NOTHING;

-- 5. Initial Bookings (In-House, Pre-Stay, Early Departure)
INSERT INTO public.room_bookings (id, reference_code, hotel_id, guest_name, guest_phone, room_number, room_category, check_in_date, check_out_date, nights, guests_count, price_per_night, total_price, special_requests, is_early_departure, actual_departure_date, early_departure_reason, status)
VALUES
    (
        'book_rossi_402',
        'SINA-4020',
        'sina_bernini_bristol',
        'Marco Rossi',
        '+39 333 1112233',
        '402',
        'panoramic_suite',
        CURRENT_DATE - INTERVAL '1 day',
        CURRENT_DATE + INTERVAL '2 days',
        3,
        2,
        750.00,
        2250.00,
        '10° Anniversario di Nozze. Giulia è celiaca.',
        FALSE,
        NULL,
        NULL,
        'checked_in'
    ),
    (
        'book_moretti_201',
        'SINA-2015',
        'sina_bernini_bristol',
        'Andrea Moretti',
        '+39 335 9988776',
        '201',
        'deluxe',
        CURRENT_DATE + INTERVAL '1 day',
        CURRENT_DATE + INTERVAL '3 days',
        2,
        1,
        350.00,
        700.00,
        'Membro Sina Privilege VIP. Transfer NCC FCO.',
        FALSE,
        NULL,
        NULL,
        'confirmed'
    ),
    (
        'book_ferri_101',
        'SINA-1018',
        'sina_bernini_bristol',
        'Roberto Ferri',
        '+39 347 1234567',
        '101',
        'superior',
        CURRENT_DATE - INTERVAL '2 days',
        CURRENT_DATE + INTERVAL '2 days',
        2,
        1,
        250.00,
        500.00,
        'Partenza anticipata registrata.',
        TRUE,
        CURRENT_DATE,
        'Rientro urgente aziendale a Milano',
        'early_departure'
    ),
    (
        'book_bianchi_301',
        'SINA-3012',
        'sina_bernini_bristol',
        'Elena Bianchi',
        '+39 340 5544332',
        '301',
        'junior_suite',
        CURRENT_DATE - INTERVAL '4 days',
        CURRENT_DATE - INTERVAL '1 day',
        3,
        4,
        480.00,
        1440.00,
        'Famiglia con due bambini. Letto supplementare richiesto.',
        FALSE,
        NULL,
        NULL,
        'checked_out'
    )
ON CONFLICT (reference_code) DO NOTHING;

-- 6. City Recommendations
INSERT INTO public.city_recommendations (id, hotel_id, category, title, description_it, description_en, tags, recommended_for, insider_tip_it)
VALUES
    (
        'rec_the_flair',
        'sina_bernini_bristol',
        'dining',
        'Cena Gourmet sul Rooftop ''The Flair''',
        'Cena a lume di candela al nostro rooftop restaurant all''ultimo piano dell''hotel, con vista mozzafiato su Roma illuminata e Piazza Barberini.',
        'Candlelight gourmet dinner at our rooftop restaurant atop the hotel, with breathtaking 360-degree views over illuminated Rome.',
        ARRAY['romantico', 'rooftop', 'vista', 'anniversario', 'alta cucina', 'in-house'],
        ARRAY['romantic_couple', 'general_leisure'],
        'Prenotiamo per voi il tavolo ad angolo verso il tramonto con servizio dedicato e opzioni 100% gluten-free.'
    ),
    (
        'rec_couple_spa_ritual',
        'sina_bernini_bristol',
        'spa_wellness',
        'Rituale di Coppia ''Sina Sensations''',
        'Percorso benessere esclusivo con bagno turco aromaterapico e massaggio rilassante di coppia con oli essenziali d''agrumi.',
        'Exclusive wellness path with aromatherapeutic Turkish bath and couple''s relaxing massage with Mediterranean citrus oils.',
        ARRAY['spa', 'coppia', 'relax', 'benessere', 'massaggi'],
        ARRAY['romantic_couple', 'wellness_seeker'],
        'Consigliato nel tardo pomeriggio prima dell''aperitivo sulla terrazza.'
    ),
    (
        'rec_galleria_borghese_vip',
        'sina_bernini_bristol',
        'city_experience',
        'Visita Esclusiva alla Galleria Borghese con Guida d''Arte',
        'Accesso riservato salta-fila ai capolavori scultorei del Bernini (Apollo e Dafne, Ratto di Proserpina) a pochi minuti a piedi dall''hotel.',
        'Skip-the-line VIP access to Gian Lorenzo Bernini''s masterpieces at Galleria Borghese, just a scenic stroll from the hotel.',
        ARRAY['bernini', 'arte', 'cultura', 'museo', 'salta la fila'],
        ARRAY['culture_explorer', 'romantic_couple'],
        'Il nostro concierge riserva i biglietti VIP esclusivi anche quando il museo risulta sold out al pubblico.'
    ),
    (
        'rec_fco_executive_transfer',
        'sina_bernini_bristol',
        'transport',
        'Transfer Privato NCC Mercedes Classe E (Aeroporto FCO)',
        'Autista privato NCC con cartello di benvenuto direttamente al terminal degli arrivi di Roma Fiumicino o Ciampino fino all''hotel.',
        'Private chauffeur service in a Mercedes E-Class directly from Rome Fiumicino (FCO) arrivals gate to the hotel.',
        ARRAY['transfer', 'aeroporto', 'fiumicino', 'fco', 'ncc', 'autista', 'puntualità'],
        ARRAY['business_solo', 'general_leisure'],
        'Autista puntuale con monitoraggio del volo in tempo reale; tariffa convenzionata fissa.'
    ),
    (
        'rec_business_express_lunch',
        'sina_bernini_bristol',
        'dining',
        'Pranzo Riservato al Lounge Bar del Bristol',
        'Ambiente riservato ed elegante ideale per colloqui o lavoro, con menu leggero e servizio veloce in 40 minuti.',
        'Private and elegant lounge environment ideal for meetings, with a curated express light lunch served in under 40 minutes.',
        ARRAY['business lunch', 'veloce', 'riservato', 'lavoro', 'wi-fi'],
        ARRAY['business_solo'],
        'Tavolo appartato con prese di corrente e connessione Wi-Fi ultra veloce garantita.'
    ),
    (
        'rec_family_gladiator_tour',
        'sina_bernini_bristol',
        'city_experience',
        'Tour Guidato per Famiglie al Colosseo e Fori Romani',
        'Esperienza interattiva con guida specializzata per ragazzi e bambini per rivivere i fasti dell''Antica Roma senza code estenuanti.',
        'Interactive family-friendly tour of the Colosseum and Roman Forum tailored for children with engaging storytelling.',
        ARRAY['famiglia', 'bambini', 'colosseo', 'roma antica', 'didattico'],
        ARRAY['family_leisure'],
        'Include mappa illustrata per i bambini e sosta gelato artigianale consigliata.'
    )
ON CONFLICT (id) DO NOTHING;

-- 7. Official FAQs
INSERT INTO public.hotel_faqs (id, hotel_id, category, question_it, answer_it, keywords)
VALUES
    ('faq_checkin', 'sina_bernini_bristol', 'orari', 'Quali sono gli orari di check-in e check-out?', 'Il check-in all''hotel è disponibile dalle ore 15:00 e il check-out entro le ore 12:00. Early check-in e late check-out disponibili su richiesta.', ARRAY['check in', 'check out', 'orari']),
    ('faq_parking', 'sina_bernini_bristol', 'parcheggio', 'Disponete di parcheggio?', 'Offriamo servizio Car Valet privato e convenzione con garage custodito con ricarica per veicoli elettrici in Piazza Barberini.', ARRAY['parcheggio', 'garage', 'valet', 'auto']),
    ('faq_rooftop', 'sina_bernini_bristol', 'rooftop', 'Quali sono gli orari del Rooftop The Flair?', 'Il nostro Rooftop Restaurant The Flair è aperto dalle 19:30 alle 23:30 per cena gourmet con vista panoramica a 360° su Roma.', ARRAY['rooftop', 'the flair', 'terrazza', 'ristorante']),
    ('faq_spa', 'sina_bernini_bristol', 'spa', 'Come funziona la spa?', 'La Sina Wellness & Spa è aperta dalle 10:00 alle 20:00 su prenotazione, con bagno turco, sauna e massaggi esclusivi di coppia.', ARRAY['spa', 'benessere', 'massaggi', 'relax']),
    ('faq_location', 'sina_bernini_bristol', 'indirizzo', 'Dove si trova l''hotel?', 'Sina Bernini Bristol si trova in Piazza Barberini 23, 00187 Roma, all''inizio di Via Veneto e a 5 minuti da Piazza di Spagna.', ARRAY['dove siete', 'indirizzo', 'posizione'])
ON CONFLICT (id) DO NOTHING;

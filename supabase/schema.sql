-- ==============================================================================
-- SINA HOTELS (SINA BERNINI BRISTOL ROMA) - MASTER DATABASE & CRM SCHEMA
-- ==============================================================================
-- Paste this script into your Supabase Dashboard -> SQL Editor to initialize
-- all hotel rooms, guest CRM, notifications, and room reservations.
--
-- Cleanup obsolete LangGraph checkpointer tables and redundant legacy views
DROP TABLE IF EXISTS public.checkpoint_writes CASCADE;
DROP TABLE IF EXISTS public.checkpoint_blobs CASCADE;
DROP TABLE IF EXISTS public.checkpoints CASCADE;
DROP TABLE IF EXISTS public.checkpoint_migrations CASCADE;
DROP VIEW IF EXISTS public.hotel_bookings CASCADE;
DROP VIEW IF EXISTS public.guests CASCADE;
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
    persona TEXT DEFAULT 'general_leisure', -- 'romantic_couple', 'business_solo', 'family_leisure', 'wellness_seeker', 'culture_explorer'
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

-- 5. CRM NOTIFICATIONS & STAFF ALERTS
CREATE TABLE IF NOT EXISTS public.crm_notifications (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT DEFAULT 'sina_bernini_bristol', -- property / hotel ID
    type TEXT NOT NULL, -- 'new_booking', 'early_departure', 'allergy_alert', 'transfer_request', 'concierge_request'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    customer_name TEXT,
    customer_phone TEXT,
    reference_code TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crm_notifications_unread 
    ON public.crm_notifications (restaurant_id, is_read, created_at DESC);

-- 6. HOTEL OFFICIAL FAQS
CREATE TABLE IF NOT EXISTS public.hotel_faqs (
    id TEXT PRIMARY KEY,
    hotel_id TEXT REFERENCES public.hotels(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    question_it TEXT NOT NULL,
    answer_it TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- INITIAL SEED DATA: SINA BERNINI BRISTOL (ROMA)
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
INSERT INTO public.crm_guests (id, phone_number, first_name, last_name, vip_tier, persona, dietary_restrictions, room_preferences, favorite_drinks, special_notes)
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
        'Festeggiano il 10° anniversario di nozze. Gradito tavolo appartato vista tramonto.'
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
        'Membro Sina Privilege VIP. Richiede sempre transfer NCC Fiumicino e massima puntualità.'
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
        'Partenza anticipata effettuata per urgenza lavorativa a Milano.'
    )
ON CONFLICT (phone_number) DO NOTHING;

-- 4. Initial Bookings (In-House, Pre-Stay, Early Departure)
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
    )
ON CONFLICT (reference_code) DO NOTHING;

-- 5. Official FAQs
INSERT INTO public.hotel_faqs (id, hotel_id, category, question_it, answer_it, keywords)
VALUES
    ('faq_checkin', 'sina_bernini_bristol', 'orari', 'Quali sono gli orari di check-in e check-out?', 'Il check-in all''hotel è disponibile dalle ore 15:00 e il check-out entro le ore 12:00. Early check-in e late check-out disponibili su richiesta.', ARRAY['check in', 'check out', 'orari']),
    ('faq_parking', 'sina_bernini_bristol', 'parcheggio', 'Disponete di parcheggio?', 'Offriamo servizio Car Valet privato e convenzione con garage custodito con ricarica per veicoli elettrici in Piazza Barberini.', ARRAY['parcheggio', 'garage', 'valet', 'auto']),
    ('faq_rooftop', 'sina_bernini_bristol', 'rooftop', 'Quali sono gli orari del Rooftop The Flair?', 'Il nostro Rooftop Restaurant The Flair è aperto dalle 19:30 alle 23:30 per cena gourmet con vista panoramica a 360° su Roma.', ARRAY['rooftop', 'the flair', 'terrazza', 'ristorante']),
    ('faq_spa', 'sina_bernini_bristol', 'spa', 'Come funziona la spa?', 'La Sina Wellness & Spa è aperta dalle 10:00 alle 20:00 su prenotazione, con bagno turco, sauna e massaggi esclusivi di coppia.', ARRAY['spa', 'benessere', 'massaggi', 'relax']),
    ('faq_location', 'sina_bernini_bristol', 'indirizzo', 'Dove si trova l''hotel?', 'Sina Bernini Bristol si trova in Piazza Barberini 23, 00187 Roma, all''inizio di Via Veneto e a 5 minuti da Piazza di Spagna.', ARRAY['dove siete', 'indirizzo', 'posizione'])
ON CONFLICT (id) DO NOTHING;

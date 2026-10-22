-- ==============================================================================
-- SUPABASE DATABASE SCHEMA FOR ITALIAN RESTAURANT AI VOICE RECEPTIONIST
-- ==============================================================================
-- Paste this script into your Supabase Dashboard -> SQL Editor to initialize
-- the business tables for Trattoria Bella Vista (or your restaurant).
--
-- NOTE: LangGraph's AsyncPostgresSaver checkpointer will automatically create
-- its own internal tables (checkpoints, checkpoint_blobs, checkpoint_writes, 
-- checkpoint_migrations) upon connection when DATABASE_URL is set in .env.
-- ==============================================================================

-- 1. RESTAURANTS TABLE
CREATE TABLE IF NOT EXISTS public.restaurants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    address TEXT,
    timezone TEXT DEFAULT 'Europe/Rome',
    slot_duration_minutes INT DEFAULT 90,
    max_party_size INT DEFAULT 10,
    shifts JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TABLES INVENTORY
CREATE TABLE IF NOT EXISTS public.tables (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT REFERENCES public.restaurants(id) ON DELETE CASCADE,
    table_number INT NOT NULL,
    min_capacity INT DEFAULT 1,
    max_capacity INT DEFAULT 4,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. RESERVATIONS
CREATE TABLE IF NOT EXISTS public.reservations (
    id TEXT PRIMARY KEY,
    reference_code TEXT UNIQUE NOT NULL,
    restaurant_id TEXT REFERENCES public.restaurants(id) ON DELETE CASCADE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    party_size INT NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TEXT NOT NULL,
    duration_minutes INT DEFAULT 90,
    table_id TEXT REFERENCES public.tables(id),
    dietary_notes TEXT,
    special_requests TEXT,
    status TEXT DEFAULT 'confirmed',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reservations_date_status 
    ON public.reservations (restaurant_id, booking_date, status);
CREATE INDEX IF NOT EXISTS idx_reservations_phone 
    ON public.reservations (customer_phone);

-- 4. CRM NOTIFICATIONS
CREATE TABLE IF NOT EXISTS public.crm_notifications (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT REFERENCES public.restaurants(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
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

-- 5. FAQS
CREATE TABLE IF NOT EXISTS public.faqs (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT REFERENCES public.restaurants(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    question_it TEXT NOT NULL,
    answer_it TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- SEED DATA: TRATTORIA BELLA VISTA
-- ==============================================================================
INSERT INTO public.restaurants (id, name, phone_number, address, timezone, slot_duration_minutes, max_party_size, shifts)
VALUES (
    'default_trattoria',
    'Trattoria Bella Vista',
    '+39 06 1234567',
    'Via Roma 42, Roma',
    'Europe/Rome',
    90,
    10,
    '[
        {"name": "lunch", "name_it": "pranzo", "start_time": "12:30", "end_time": "15:00", "last_seating_time": "14:00"},
        {"name": "dinner", "name_it": "cena", "start_time": "19:30", "end_time": "23:00", "last_seating_time": "22:00"}
    ]'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- Tables
INSERT INTO public.tables (id, restaurant_id, table_number, min_capacity, max_capacity, is_active)
VALUES
    ('T1', 'default_trattoria', 1, 1, 2, TRUE),
    ('T2', 'default_trattoria', 2, 1, 2, TRUE),
    ('T3', 'default_trattoria', 3, 3, 4, TRUE),
    ('T4', 'default_trattoria', 4, 3, 4, TRUE),
    ('T5', 'default_trattoria', 5, 5, 6, TRUE),
    ('T6', 'default_trattoria', 6, 7, 10, TRUE)
ON CONFLICT (id) DO NOTHING;

-- FAQs
INSERT INTO public.faqs (id, restaurant_id, category, question_it, answer_it, keywords)
VALUES
    ('faq_parking', 'default_trattoria', 'parcheggio', 'Dove posso parcheggiare?', 'Abbiamo una convenzione con il Garage Garibaldi a 50 metri dal ristorante. La prima ora è gratuita per i nostri ospiti.', ARRAY['parcheggio', 'garage', 'posto auto']),
    ('faq_dresscode', 'default_trattoria', 'dress_code', 'Qual è il codice di abbigliamento?', 'Non richiediamo un abbigliamento formale; uno stile casual curato è perfetto.', ARRAY['abbigliamento', 'dress code', 'vestirsi']),
    ('faq_pets', 'default_trattoria', 'animali', 'Accettate animali domestici?', 'I cani di piccola e media taglia sono benvenuti nei nostri tavoli all''aperto e nella sala veranda.', ARRAY['cane', 'cani', 'animali', 'pet']),
    ('faq_allergies', 'default_trattoria', 'allergie', 'Avete opzioni senza glutine o per allergie?', 'Proponiamo alternative senza glutine e per vegetariani. Raccomandiamo sempre di segnalare le allergie all''arrivo.', ARRAY['senza glutine', 'celiachia', 'allergia', 'vegetariano']),
    ('faq_location', 'default_trattoria', 'indirizzo', 'Dove vi trovate?', 'Siamo in Via Roma 42, a 5 minuti a piedi da Piazza del Popolo.', ARRAY['dove siete', 'indirizzo', 'posizione'])
ON CONFLICT (id) DO NOTHING;

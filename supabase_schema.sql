-- ============================================================
-- Blood Donor Management and Tracking System
-- Supabase PostgreSQL Schema + RLS Policies
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";



-- ============================================================
-- TABLE: profiles
-- ============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    role        TEXT NOT NULL DEFAULT 'donor' CHECK (role IN ('admin', 'donor')),
    phone       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FUNCTION: is_admin()
-- Bypasses RLS to avoid infinite recursion when checking roles
-- ============================================================
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid() AND role = 'admin'
    );
$$ LANGUAGE sql SECURITY DEFINER SET search_path = public;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles"
    ON public.profiles FOR SELECT
    USING (
        public.is_admin()
    );

CREATE POLICY "Admins can update all profiles"
    ON public.profiles FOR UPDATE
    USING (
        public.is_admin()
    );

-- ============================================================
-- TABLE: donors
-- ============================================================
CREATE TABLE IF NOT EXISTS public.donors (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id          UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    full_name           TEXT NOT NULL,
    date_of_birth       DATE NOT NULL,
    gender              TEXT NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    blood_group         TEXT NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','O+','O-','AB+','AB-')),
    phone               TEXT NOT NULL,
    email               TEXT,
    address             TEXT,
    city                TEXT,
    state               TEXT,
    is_eligible         BOOLEAN DEFAULT TRUE,
    last_donation_date  DATE,
    total_donations     INTEGER DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.donors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view donors"
    ON public.donors FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can insert donors"
    ON public.donors FOR INSERT
    WITH CHECK (
        public.is_admin()
    );

CREATE POLICY "Admins can update donors"
    ON public.donors FOR UPDATE
    USING (
        public.is_admin()
    );

CREATE POLICY "Admins can delete donors"
    ON public.donors FOR DELETE
    USING (
        public.is_admin()
    );

-- ============================================================
-- TABLE: donations
-- ============================================================
CREATE TABLE IF NOT EXISTS public.donations (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id          UUID NOT NULL REFERENCES public.donors(id) ON DELETE CASCADE,
    donation_date     DATE NOT NULL,
    blood_group       TEXT NOT NULL,
    units_donated     NUMERIC(4,2) DEFAULT 1.0,
    donation_center   TEXT,
    hemoglobin_level  NUMERIC(4,1),
    blood_pressure    TEXT,
    status            TEXT DEFAULT 'completed' CHECK (status IN ('completed', 'deferred', 'pending')),
    notes             TEXT,
    recorded_by       UUID REFERENCES public.profiles(id),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.donations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view donations"
    ON public.donations FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can manage donations"
    ON public.donations FOR ALL
    USING (
        public.is_admin()
    );

-- ============================================================
-- TABLE: blood_requests
-- ============================================================
CREATE TABLE IF NOT EXISTS public.blood_requests (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_name    TEXT NOT NULL,
    requester_phone   TEXT NOT NULL,
    requester_email   TEXT,
    blood_group       TEXT NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','O+','O-','AB+','AB-')),
    units_required    INTEGER NOT NULL,
    urgency           TEXT DEFAULT 'normal' CHECK (urgency IN ('critical', 'urgent', 'normal')),
    hospital_name     TEXT,
    required_by_date  DATE,
    status            TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'fulfilled', 'cancelled')),
    notes             TEXT,
    requested_by      UUID REFERENCES public.profiles(id),
    fulfilled_by      UUID REFERENCES public.donors(id),
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.blood_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view blood requests"
    ON public.blood_requests FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert blood requests"
    ON public.blood_requests FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Admins can update blood requests"
    ON public.blood_requests FOR UPDATE
    USING (
        public.is_admin()
    );

CREATE POLICY "Admins can delete blood requests"
    ON public.blood_requests FOR DELETE
    USING (
        public.is_admin()
    );

-- ============================================================
-- TABLE: blood_inventory
-- ============================================================
CREATE TABLE IF NOT EXISTS public.blood_inventory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blood_group     TEXT UNIQUE NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','O+','O-','AB+','AB-')),
    units_available NUMERIC(6,2) DEFAULT 0,
    last_updated    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.blood_inventory ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view inventory"
    ON public.blood_inventory FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can manage inventory"
    ON public.blood_inventory FOR ALL
    USING (
        public.is_admin()
    );

-- ============================================================
-- SEED: Blood Inventory (one row per blood group)
-- ============================================================
INSERT INTO public.blood_inventory (blood_group, units_available) VALUES
    ('A+',  0),
    ('A-',  0),
    ('B+',  0),
    ('B-',  0),
    ('O+',  0),
    ('O-',  0),
    ('AB+', 0),
    ('AB-', 0)
ON CONFLICT (blood_group) DO NOTHING;

-- ============================================================
-- FUNCTION: Auto-create profile on user signup
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'Unknown'),
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'role', 'donor')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- FUNCTION: Update updated_at timestamp automatically
-- ============================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_donors_updated_at
    BEFORE UPDATE ON public.donors
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_blood_requests_updated_at
    BEFORE UPDATE ON public.blood_requests
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

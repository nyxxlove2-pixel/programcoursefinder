-- Program Course Finder: database schema for Supabase (PostgreSQL)
-- Paste this whole file into Supabase > SQL Editor > New query > Run.
-- Roles: user, organization (no administrator role).

-- =====================================================
-- 1. ACCOUNTS
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email          TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    full_name      TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('user', 'organization')),
    avatar_url     TEXT,  -- profile photo in Supabase Storage (bucket profile-images)
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Extra details for the "user" role
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id         BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    interests       TEXT,
    bio             TEXT,
    hometown        TEXT,
    address         TEXT,
    latitude        NUMERIC(9, 6),
    longitude       NUMERIC(9, 6),
    share_location  BOOLEAN NOT NULL DEFAULT FALSE,  -- location is used only with consent
    cover_url       TEXT                            -- background image on the profile page
);

-- =====================================================
-- 2. ORGANIZATIONS AND VERIFICATION
-- =====================================================

CREATE TABLE IF NOT EXISTS organizations (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id       BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    description    TEXT,
    phone          TEXT,
    email          TEXT,
    address        TEXT,
    latitude       NUMERIC(9, 6),
    longitude      NUMERIC(9, 6),
    website        TEXT,
    facebook_url   TEXT,
    instagram_url  TEXT,
    tiktok_url     TEXT,
    youtube_url    TEXT,
    logo_url       TEXT,  -- logo and cover image in Supabase Storage (bucket profile-images)
    cover_url      TEXT,
    status         TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'approved', 'needs_changes', 'rejected')),
    status_reason  TEXT,           -- shown when status is needs_changes or rejected
    verified_at    TIMESTAMPTZ,    -- set when approved
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS verification_documents (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id  BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    doc_type         TEXT NOT NULL CHECK (doc_type IN (
                         'government_recognition',
                         'sec_registration',
                         'authorization_letter',
                         'valid_id',
                         'proof_of_official_channels')),
    file_url         TEXT NOT NULL,
    uploaded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at       TIMESTAMPTZ,  -- documents are re-checked yearly
    UNIQUE (organization_id, doc_type)
);

-- =====================================================
-- 3. COURSES
-- =====================================================

CREATE TABLE IF NOT EXISTS courses (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id  BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name             TEXT NOT NULL,
    description      TEXT,
    yearly_tuition   NUMERIC(12, 2) NOT NULL CHECK (yearly_tuition >= 0),
    term_tuition     NUMERIC(12, 2) CHECK (term_tuition >= 0),
    last_updated     TIMESTAMPTZ NOT NULL DEFAULT now(),  -- shown to users; old ones get flagged
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Images and videos for a course (a video can be a YouTube/Facebook link)
CREATE TABLE IF NOT EXISTS course_media (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_id   BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    media_type  TEXT NOT NULL CHECK (media_type IN ('image', 'video')),
    url         TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- 4. REVIEWS
-- =====================================================

CREATE TABLE IF NOT EXISTS reviews (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_id   BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (course_id, user_id)  -- one review per user per course
);

-- Replies from the organization (organizations can reply but not delete reviews)
CREATE TABLE IF NOT EXISTS review_replies (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id   BIGINT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Like / dislike on a review (one reaction per user per review)
CREATE TABLE IF NOT EXISTS review_reactions (
    review_id  BIGINT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reaction   TEXT NOT NULL CHECK (reaction IN ('like', 'dislike')),
    PRIMARY KEY (review_id, user_id)
);

-- Reports for false information or abusive content
CREATE TABLE IF NOT EXISTS reports (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reporter_id  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type  TEXT NOT NULL CHECK (target_type IN ('review', 'course', 'organization')),
    target_id    BIGINT NOT NULL,
    reason       TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- 5. DASHBOARD AND AI
-- =====================================================

CREATE TABLE IF NOT EXISTS notifications (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message     TEXT NOT NULL,
    link        TEXT,
    is_read     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Saved AI summaries (cached so we stay inside the Groq free tier)
CREATE TABLE IF NOT EXISTS review_summaries (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_id      BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    period_type    TEXT NOT NULL CHECK (period_type IN ('monthly', 'yearly')),
    period_start   DATE NOT NULL,
    average_rating NUMERIC(3, 2),
    praises        TEXT,
    complaints     TEXT,
    changes        TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (course_id, period_type, period_start)
);

-- AI assistant chats: one conversation per topic, one row per question and answer.
-- sources keeps the cited courses as [{"id", "name", "college"}] so old answers still show them.
CREATE TABLE IF NOT EXISTS ai_conversations (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_messages (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id  BIGINT NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    question         TEXT NOT NULL,
    answer           TEXT NOT NULL,
    sources          JSONB NOT NULL DEFAULT '[]',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Paid ads: a banner image or a YouTube video. Shown with a "Sponsored" label,
-- approved by the developer in Django admin, and never used by the AI.
CREATE TABLE IF NOT EXISTS ads (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id  BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    course_id        BIGINT REFERENCES courses(id) ON DELETE SET NULL,  -- optional: ad links to this course
    title            TEXT NOT NULL,
    ad_type          TEXT NOT NULL CHECK (ad_type IN ('banner', 'video')),
    media_url        TEXT NOT NULL,  -- image link for a banner, YouTube link for a video
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- 6. HANDY VIEW: average rating per course
-- =====================================================

CREATE OR REPLACE VIEW course_ratings AS
SELECT
    c.id AS course_id,
    COALESCE(ROUND(AVG(r.rating), 2), 0) AS average_rating,
    COUNT(r.id) AS review_count
FROM courses c
LEFT JOIN reviews r ON r.course_id = c.id
GROUP BY c.id;

-- =====================================================
-- 7. AUTO-UPDATE courses.last_updated
-- =====================================================

CREATE OR REPLACE FUNCTION set_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS courses_set_last_updated ON courses;
CREATE TRIGGER courses_set_last_updated
BEFORE UPDATE ON courses
FOR EACH ROW EXECUTE FUNCTION set_last_updated();

-- =====================================================
-- 8. INDEXES (faster search and joins)
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_organizations_status   ON organizations(status);
CREATE INDEX IF NOT EXISTS idx_courses_organization   ON courses(organization_id);
CREATE INDEX IF NOT EXISTS idx_courses_tuition        ON courses(yearly_tuition);
CREATE INDEX IF NOT EXISTS idx_courses_name           ON courses(lower(name));
CREATE INDEX IF NOT EXISTS idx_reviews_course         ON reviews(course_id);
CREATE INDEX IF NOT EXISTS idx_replies_review         ON review_replies(review_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user     ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_reports_status         ON reports(status);
CREATE INDEX IF NOT EXISTS idx_ads_status             ON ads(status);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_user  ON ai_conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_messages_chat       ON ai_messages(conversation_id);

-- =====================================================
-- 9. SECURITY
-- =====================================================
-- Turn on Row Level Security with no policies. This blocks Supabase's public
-- API from reading these tables. Django connects with the database password
-- (postgres role), which is not affected, so the app still works.

ALTER TABLE users                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations          ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses                ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_media           ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews                ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_replies         ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_reactions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports                ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications          ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_summaries       ENABLE ROW LEVEL SECURITY;
ALTER TABLE ads                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_conversations       ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_messages            ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 10. AFTER "python manage.py migrate"
-- =====================================================
-- Django creates its own tables (auth_*, django_*: sessions, admin login).
-- Run this once afterwards so they are also hidden from the public API.

DO $$
DECLARE t TEXT;
BEGIN
    FOR t IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
          AND (tablename LIKE 'auth\_%' OR tablename LIKE 'django\_%')
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;
END $$;

-- =====================================================
-- 11. PROFILE IMAGES
-- =====================================================
-- Photos, logos, and cover images are stored in Supabase Storage (Vercel's disk is
-- read-only). This makes a public bucket for them: 5 MB max, images only.
-- The ALTER lines add the image columns to a database made before they existed.

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('profile-images', 'profile-images', TRUE, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO NOTHING;

ALTER TABLE users         ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS cover_url  TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS logo_url   TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS cover_url  TEXT;

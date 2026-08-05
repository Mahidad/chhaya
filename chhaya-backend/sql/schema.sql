-- =============================================================================
-- Chhaya – PostgreSQL schema (Module 1)
-- Run against a fresh database:
--   psql -U <user> -d chhaya -f sql/schema.sql
--
-- Module 1 Feature 4 (Amiyo): study_sessions + study_guide_views
--   added 2026-08-05. quiz_results removed (was wrong feature).
--
-- Safe to re-run: every statement uses IF NOT EXISTS / IF EXISTS.
-- gen_random_uuid() requires the pgcrypto extension (bundled with every
-- standard Postgres install since v8.3).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id               TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    full_name        TEXT        NOT NULL,
    email            TEXT        NOT NULL UNIQUE,
    hashed_password  TEXT        NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ---------------------------------------------------------------------------
-- reference_sources
-- One row = one YouTube video / playlist / course link a student adds.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reference_sources (
    id            TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title         TEXT        NOT NULL,
    source_type   TEXT        NOT NULL DEFAULT 'youtube_playlist',
    url           TEXT        NOT NULL,
    status        TEXT        NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reference_sources_user_id ON reference_sources (user_id);

-- ---------------------------------------------------------------------------
-- videos
-- One row per video that belongs to a reference source.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
    id                TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source_id         TEXT    NOT NULL REFERENCES reference_sources (id) ON DELETE CASCADE,
    youtube_video_id  TEXT    NOT NULL,
    title             TEXT    NOT NULL,
    order_index       INTEGER NOT NULL DEFAULT 0,
    duration_seconds  INTEGER,
    transcript_text   TEXT,
    transcript_status TEXT    NOT NULL DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_videos_source_id ON videos (source_id);

-- ---------------------------------------------------------------------------
-- teacher_profiles
-- The structured teaching-style fingerprint Gemini derives from transcripts.
-- One source → at most one profile (UNIQUE on source_id).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS teacher_profiles (
    id                TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id           TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    source_id         TEXT        NOT NULL UNIQUE REFERENCES reference_sources (id) ON DELETE CASCADE,
    display_name      TEXT        NOT NULL,
    is_favorite       BOOLEAN     NOT NULL DEFAULT FALSE,
    pacing            TEXT,
    vocabulary_level  TEXT,
    analogy_frequency TEXT,
    example_density   TEXT,
    raw_style_profile JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teacher_profiles_user_id ON teacher_profiles (user_id);

-- ---------------------------------------------------------------------------
-- study_guides
-- AI-generated study guide, scoped to a teacher profile's style.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_guides (
    id                    TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id               TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    teacher_profile_id    TEXT        NOT NULL REFERENCES teacher_profiles (id) ON DELETE CASCADE,
    topic                 TEXT        NOT NULL,
    depth                 TEXT        NOT NULL DEFAULT 'standard',
    include_formula_sheet BOOLEAN     NOT NULL DEFAULT FALSE,
    include_bangla        BOOLEAN     NOT NULL DEFAULT FALSE,
    status                TEXT        NOT NULL DEFAULT 'pending',
    error_message         TEXT,
    content               TEXT,
    formula_sheet_content TEXT,
    bangla_content        TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_study_guides_user_id ON study_guides (user_id);

-- ---------------------------------------------------------------------------
-- exam_papers
-- Scanned past-paper uploads; extracted_text is populated by OCR.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exam_papers (
    id             TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id        TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title          TEXT        NOT NULL,
    course         TEXT,
    file_path      TEXT        NOT NULL,
    status         TEXT        NOT NULL DEFAULT 'pending',
    error_message  TEXT,
    extracted_text TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exam_papers_user_id ON exam_papers (user_id);

-- ---------------------------------------------------------------------------
-- study_sessions  (Module 1 Feature 4 – Amiyo)
-- One row per learning session a student opens.
-- started_at is set on INSERT; ended_at + duration_secs are set when the
-- student closes the session via PUT /progress/study-sessions/{id}/end.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_sessions (
    id            TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at      TIMESTAMPTZ,
    duration_secs INTEGER,    -- seconds; NULL while session is still open
    is_seed       BOOLEAN     NOT NULL DEFAULT FALSE  -- TRUE for demo data inserted by /seed-sample-data
);

CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id    ON study_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_started_at ON study_sessions (started_at);
-- Add is_seed to existing tables that were created before this column existed
ALTER TABLE study_sessions ADD COLUMN IF NOT EXISTS is_seed BOOLEAN NOT NULL DEFAULT FALSE;

-- ---------------------------------------------------------------------------
-- study_guide_views  (Module 1 Feature 4 – Amiyo)
-- One row each time a student opens a completed guide's detail page.
-- Recorded silently (fire-and-forget) by GuideDetailPage.jsx via
-- POST /progress/study-guide-views.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_guide_views (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id         TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    study_guide_id  TEXT        NOT NULL,
    viewed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_seed         BOOLEAN     NOT NULL DEFAULT FALSE  -- TRUE for demo data inserted by /seed-sample-data
);

CREATE INDEX IF NOT EXISTS idx_study_guide_views_user_id  ON study_guide_views (user_id);
CREATE INDEX IF NOT EXISTS idx_study_guide_views_viewed_at ON study_guide_views (viewed_at);
-- Add is_seed to existing tables that were created before this column existed
ALTER TABLE study_guide_views ADD COLUMN IF NOT EXISTS is_seed BOOLEAN NOT NULL DEFAULT FALSE;

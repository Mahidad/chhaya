-- =============================================================================
-- Chhaya – PostgreSQL schema (Module 1)
-- Run against a fresh database:
--   psql -U <user> -d chhaya -f sql/schema.sql
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
-- quiz_results
-- One row per quiz attempt; aggregated by progress_service into weak topics.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quiz_results (
    id            TEXT             PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       TEXT             NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    topic         TEXT             NOT NULL,
    course        TEXT,
    score_percent DOUBLE PRECISION NOT NULL,
    taken_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id ON quiz_results (user_id);

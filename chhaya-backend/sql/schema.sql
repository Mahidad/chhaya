

CREATE EXTENSION IF NOT EXISTS pgcrypto;


CREATE TABLE IF NOT EXISTS users (
    id               TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    full_name        TEXT        NOT NULL,
    email            TEXT        NOT NULL UNIQUE,
    hashed_password  TEXT        NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

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

CREATE TABLE IF NOT EXISTS likely_questions (
    id                 TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id            TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title              TEXT        NOT NULL,
    course             TEXT,
    status             TEXT        NOT NULL DEFAULT 'pending',
    error_message      TEXT,
    source_paper_count INTEGER     NOT NULL,
    source_paper_ids   JSONB       NOT NULL DEFAULT '{"ids": []}'::jsonb,
    analysis           JSONB,
    predicted_questions JSONB,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_likely_questions_user_id ON likely_questions (user_id);


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

-- ---------------------------------------------------------------------------
-- courses  (Module 2 – Lamia)
-- Organizational wrapper: a student creates Courses, each containing Chapters.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id     TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title       TEXT        NOT NULL,
    order_index INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_courses_user_id ON courses (user_id);

-- ---------------------------------------------------------------------------
-- chapters  (Module 2 – Lamia)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chapters (
    id          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id     TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    course_id   TEXT        NOT NULL REFERENCES courses (id) ON DELETE CASCADE,
    title       TEXT        NOT NULL,
    order_index INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chapters_course_id ON chapters (course_id);

-- Add optional chapter_id to study_guides so a guide can be filed into a chapter
ALTER TABLE study_guides ADD COLUMN IF NOT EXISTS chapter_id TEXT REFERENCES chapters (id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- notes  (Module 2 – Lamia)
-- Uploaded or typed personal notes, attached to a chapter.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notes (
    id           TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id      TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    chapter_id   TEXT        NOT NULL REFERENCES chapters (id) ON DELETE CASCADE,
    title        TEXT        NOT NULL,
    note_type    TEXT        NOT NULL DEFAULT 'text',
    text_content TEXT,
    file_path    TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_chapter_id ON notes (chapter_id);

-- ---------------------------------------------------------------------------
-- highlights  (Module 2 – Lamia)
-- Text selections highlighted by the student inside a study guide or note.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS highlights (
    id           TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id      TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    chapter_id   TEXT        NOT NULL REFERENCES chapters (id) ON DELETE CASCADE,
    content_type TEXT        NOT NULL,
    content_id   TEXT        NOT NULL,
    quoted_text  TEXT        NOT NULL,
    color        TEXT        NOT NULL DEFAULT 'amber',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_highlights_content ON highlights (content_type, content_id);

-- ---------------------------------------------------------------------------
-- sticky_notes  (Module 2 – Lamia)
-- Short free-text annotations anchored to content inside a chapter.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sticky_notes (
    id           TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id      TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    chapter_id   TEXT        NOT NULL REFERENCES chapters (id) ON DELETE CASCADE,
    content_type TEXT        NOT NULL,
    content_id   TEXT        NOT NULL,
    body         TEXT        NOT NULL,
    anchor_text  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sticky_notes_content ON sticky_notes (content_type, content_id);

-- ---------------------------------------------------------------------------
-- glossary_entries  (Module 2 – Lamia)
-- Personal vocabulary list per chapter, entries sourced from WordNet or custom.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS glossary_entries (
    id             TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id        TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    chapter_id     TEXT        NOT NULL REFERENCES chapters (id) ON DELETE CASCADE,
    term           TEXT        NOT NULL,
    definition     TEXT        NOT NULL,
    part_of_speech TEXT,
    source         TEXT        NOT NULL DEFAULT 'wordnet',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_glossary_entries_chapter_id ON glossary_entries (chapter_id);

-- Module 2 fix -- 2026-08-12: sticky notes removed as a feature.
DROP TABLE IF EXISTS sticky_notes;

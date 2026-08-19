-- =============================================================================
-- Chhaya – PostgreSQL schema
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
-- study_groups
-- The creator is automatically added as the first member.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_groups (
    id          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    creator_id  TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name        TEXT        NOT NULL,
    description TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_group_members (
    group_id TEXT NOT NULL REFERENCES study_groups (id) ON DELETE CASCADE,
    user_id  TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE IF NOT EXISTS study_group_invitations (
    id                 TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    group_id           TEXT        NOT NULL REFERENCES study_groups (id) ON DELETE CASCADE,
    invited_user_id    TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    invited_by_user_id TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    status             TEXT        NOT NULL DEFAULT 'pending',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_group_join_requests (
    id         TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    group_id   TEXT        NOT NULL REFERENCES study_groups (id) ON DELETE CASCADE,
    user_id    TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    status     TEXT        NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (group_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_study_groups_creator_id ON study_groups (creator_id);
CREATE INDEX IF NOT EXISTS idx_study_group_invitations_user_id ON study_group_invitations (invited_user_id);

CREATE TABLE IF NOT EXISTS study_group_messages (
    id         TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    group_id   TEXT        NOT NULL REFERENCES study_groups (id) ON DELETE CASCADE,
    user_id    TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    content    TEXT        NOT NULL,
    is_pinned  BOOLEAN     NOT NULL DEFAULT FALSE,
    pinned_by_user_id TEXT REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Needed when this feature is added to an existing database.
ALTER TABLE study_group_messages
    ADD COLUMN IF NOT EXISTS pinned_by_user_id TEXT REFERENCES users (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_study_group_messages_group_id ON study_group_messages (group_id);

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
-- teacher_profiles
-- The structured teaching-style fingerprint Gemini derives from transcripts.
-- source_id is NOT unique: a playlist can have more than one instructor,
-- and each detected instructor gets their own profile. See
-- app/services/reference_source_service.py.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS teacher_profiles (
    id                TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id           TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    source_id         TEXT        NOT NULL REFERENCES reference_sources (id) ON DELETE CASCADE,
    channel_name      TEXT,
    display_name      TEXT        NOT NULL,
    is_favorite       BOOLEAN     NOT NULL DEFAULT FALSE,
    is_saved          BOOLEAN     NOT NULL DEFAULT FALSE,
    pacing            TEXT,
    vocabulary_level  TEXT,
    analogy_frequency TEXT,
    example_density   TEXT,
    raw_style_profile JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- If you already ran the old version of this file (source_id UNIQUE),
-- run this once by hand to drop the old constraint instead of dropping
-- the table:
--   ALTER TABLE teacher_profiles DROP CONSTRAINT IF EXISTS teacher_profiles_source_id_key;
--   ALTER TABLE teacher_profiles ADD COLUMN IF NOT EXISTS channel_name TEXT;

CREATE INDEX IF NOT EXISTS idx_teacher_profiles_user_id ON teacher_profiles (user_id);

CREATE INDEX IF NOT EXISTS idx_teacher_profiles_source_id ON teacher_profiles (source_id);

-- ---------------------------------------------------------------------------
-- videos
-- One row per video that belongs to a reference source.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
    id                  TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source_id           TEXT    NOT NULL REFERENCES reference_sources (id) ON DELETE CASCADE,
    teacher_profile_id  TEXT    REFERENCES teacher_profiles (id) ON DELETE SET NULL,
    youtube_video_id    TEXT    NOT NULL,
    channel_name        TEXT,
    title               TEXT    NOT NULL,
    order_index         INTEGER NOT NULL DEFAULT 0,
    duration_seconds    INTEGER,
    transcript_text     TEXT,
    transcript_status   TEXT    NOT NULL DEFAULT 'pending'
);

-- If you already ran the old version of this file, add the two new
-- columns by hand instead of dropping the table:
--   ALTER TABLE videos ADD COLUMN IF NOT EXISTS channel_name TEXT;
--   ALTER TABLE videos ADD COLUMN IF NOT EXISTS teacher_profile_id TEXT REFERENCES teacher_profiles(id) ON DELETE SET NULL;
-- (run these AFTER the teacher_profiles block above, since the FK needs
-- that table to already exist)

CREATE INDEX IF NOT EXISTS idx_videos_source_id ON videos (source_id);
-- Backs the "already extracted" duplicate check in
-- reference_source_service.py -- is this youtube_video_id already
-- ingested anywhere for this user, regardless of which source.
CREATE INDEX IF NOT EXISTS idx_videos_youtube_video_id ON videos (youtube_video_id);

-- ---------------------------------------------------------------------------
-- preference_profiles
-- One row per user: a weighted-average "style fingerprint" of what this
-- student actually prefers, computed from every profile in their Style
-- Library (see app/services/preference_service.py). Scores are 0-100 on
-- the same scale the frontend already uses for meters (low=30ish,
-- medium=60ish, high=88ish), so a candidate profile's scores can be
-- compared to these directly with simple arithmetic -- no AI call needed.
-- Recomputed (not appended to) every time it changes -- one row per user,
-- always overwritten in place.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS preference_profiles (
    id               TEXT             PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id          TEXT             NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
    pacing_score     DOUBLE PRECISION NOT NULL,
    vocabulary_score DOUBLE PRECISION NOT NULL,
    analogy_score    DOUBLE PRECISION NOT NULL,
    example_score    DOUBLE PRECISION NOT NULL,
    profile_count    INTEGER          NOT NULL,
    updated_at       TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_preference_profiles_user_id ON preference_profiles (user_id);

-- ---------------------------------------------------------------------------
-- code_style_profiles
-- A coder's style, extracted from a pasted sample -- see
-- app/utils/code_style_analyzer.py. Structurally separate from
-- teacher_profiles (different fields entirely: indentation, naming
-- convention, brace style vs. pacing/analogies), even though both show
-- up in the same Style Library UI under a tab. sample_code is kept so
-- the profile can be re-analyzed later if the analyzer heuristics improve.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS code_style_profiles (
    id                    TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id               TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    label                 TEXT        NOT NULL,
    language              TEXT        NOT NULL,
    indent_style          TEXT        NOT NULL,
    indent_size           INTEGER     NOT NULL,
    naming_convention     TEXT        NOT NULL,
    brace_style           TEXT,
    loop_style            TEXT        NOT NULL DEFAULT 'none',
    branching_style       TEXT        NOT NULL DEFAULT 'none',
    cyclomatic_complexity INTEGER     NOT NULL DEFAULT 1,
    max_nesting_depth     INTEGER     NOT NULL DEFAULT 0,
    comment_density       DOUBLE PRECISION NOT NULL,
    avg_line_length       DOUBLE PRECISION NOT NULL,
    blank_line_frequency  DOUBLE PRECISION NOT NULL,
    sample_code           TEXT        NOT NULL,
    is_favorite           BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_code_style_profiles_user_id ON code_style_profiles (user_id);

-- ---------------------------------------------------------------------------
-- code_conversions
-- History of both modes of the HLL Code Converter: "translate" (existing
-- source_code -> target_language) and "solve" (problem_statement ->
-- target_language, no source code). mapping is a JSON array of
-- {source_lines: [start,end], output_lines: [start,end], description}
-- blocks Gemini returns alongside the code, used for click-to-highlight
-- on the frontend -- see app/services/code_conversion_service.py.
-- ---------------------------------------------------------------------------
-- ---------------------------------------------------------------------------
-- code_workspace_folders
-- Shared storage/organization system for Code Studio (converter + solver +
-- visualizer). One flat list of folders per user -- no nesting, on purpose,
-- to keep "where did I save that" a one-level lookup rather than a file
-- tree a student has to remember the path through. Both code_conversions
-- and code_visualizations reference this table via a nullable folder_id;
-- anything with folder_id = NULL shows up under "Unfiled" in the UI.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS code_workspace_folders (
    id         TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name       TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_code_workspace_folders_user_id ON code_workspace_folders (user_id);

CREATE TABLE IF NOT EXISTS code_conversions (
    id                    TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id               TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    mode                  TEXT        NOT NULL,
    source_language       TEXT,
    target_language       TEXT        NOT NULL,
    source_code           TEXT,
    problem_statement     TEXT,
    code_style_profile_id TEXT        REFERENCES code_style_profiles (id) ON DELETE SET NULL,
    folder_id             TEXT        REFERENCES code_workspace_folders (id) ON DELETE SET NULL,
    title                 TEXT,
    is_favorite           BOOLEAN     NOT NULL DEFAULT FALSE,
    status                TEXT        NOT NULL DEFAULT 'pending',
    error_message         TEXT,
    output_code           TEXT,
    mapping               JSONB,
    explanation           TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_code_conversions_user_id ON code_conversions (user_id);
CREATE INDEX IF NOT EXISTS idx_code_conversions_folder_id ON code_conversions (folder_id);

-- Add title/is_favorite to tables created before the folder system existed.
-- CREATE TABLE IF NOT EXISTS above is a no-op on an existing table, so a
-- database built before those columns were added never gained them, and
-- PATCHing a conversion's name failed with "column title does not exist"
-- while the read path quietly reported title=NULL (the dataclass defaults
-- it). code_visualizations was created later and already has both.
ALTER TABLE code_conversions ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE code_conversions ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN NOT NULL DEFAULT FALSE;

-- ---------------------------------------------------------------------------
-- code_visualizations
-- Code Studio's third part: an AI-narrated step-by-step execution trace
-- (line number + variable values + a short description per step), shown
-- as a variable-watch table on the frontend. See
-- app/services/code_visualization_service.py for why this is
-- AI-simulated rather than a real sandboxed execution, and for how the
-- prompt is written to keep the trace as accurate as possible despite that.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS code_visualizations (
    id             TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id        TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    language       TEXT        NOT NULL,
    source_code    TEXT        NOT NULL,
    folder_id      TEXT        REFERENCES code_workspace_folders (id) ON DELETE SET NULL,
    title          TEXT,
    is_favorite    BOOLEAN     NOT NULL DEFAULT FALSE,
    status         TEXT        NOT NULL DEFAULT 'pending',
    error_message  TEXT,
    trace          JSONB,
    explanation    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_code_visualizations_user_id ON code_visualizations (user_id);
CREATE INDEX IF NOT EXISTS idx_code_visualizations_folder_id ON code_visualizations (folder_id);

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

CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON study_sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_study_sessions_started_at ON study_sessions (started_at);
-- Add is_seed to existing tables that were created before this column existed
ALTER TABLE study_sessions
ADD COLUMN IF NOT EXISTS is_seed BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS study_guide_views (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id         TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    study_guide_id  TEXT        NOT NULL,
    viewed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_seed         BOOLEAN     NOT NULL DEFAULT FALSE  -- TRUE for demo data inserted by /seed-sample-data
);

CREATE INDEX IF NOT EXISTS idx_study_guide_views_user_id ON study_guide_views (user_id);

CREATE INDEX IF NOT EXISTS idx_study_guide_views_viewed_at ON study_guide_views (viewed_at);
-- Add is_seed to existing tables that were created before this column existed
ALTER TABLE study_guide_views ADD COLUMN IF NOT EXISTS is_seed BOOLEAN NOT NULL DEFAULT FALSE;


-- ---------------------------------------------------------------------------
-- review_schedules  (Module 2 Feature 4 – Amiyo)
-- One review entry per user/study guide. A completed-guide view inserts this
-- record once; later recall ratings update its SM-2 interval and due date.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_schedules (
    id                TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id           TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    study_guide_id    TEXT        NOT NULL REFERENCES study_guides (id) ON DELETE CASCADE,
    topic             TEXT        NOT NULL,
    next_review_date  DATE        NOT NULL DEFAULT CURRENT_DATE,
    interval_days     INTEGER     NOT NULL DEFAULT 0,
    ease_factor       DOUBLE PRECISION NOT NULL DEFAULT 2.5,
    review_count      INTEGER     NOT NULL DEFAULT 0,
    last_reviewed_on  DATE,
    last_reminded_on  DATE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, study_guide_id)
);

CREATE INDEX IF NOT EXISTS idx_review_schedules_user_due
    ON review_schedules (user_id, next_review_date);
ALTER TABLE study_guide_views
ADD COLUMN IF NOT EXISTS is_seed BOOLEAN NOT NULL DEFAULT FALSE;

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
ALTER TABLE study_guides
ADD COLUMN IF NOT EXISTS chapter_id TEXT REFERENCES chapters (id) ON DELETE SET NULL;

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

-- Module 2 fix -- 2026-08-12: sticky notes removed as a feature. The CREATE
-- that used to sit above glossary_entries is gone; this DROP stays so that
-- databases created before that date lose the table on the next schema run.
DROP TABLE IF EXISTS sticky_notes;

-- ---------------------------------------------------------------------------
-- practice_problems
-- The problem bank behind Code Studio's Practice tab. Populated once from
-- a public LeetCode dataset (see scripts/import_practice_problems.py) --
-- NOT scraped live from leetcode.com, which their ToS prohibits and which
-- would make the content someone else's copyrighted material. Because
-- this is a static import rather than a live mirror, there is deliberately
-- no periodic sync job and no response cache to maintain: the data doesn't
-- change under us.
--
-- Shared across all users (no user_id) -- this is reference data, not
-- per-student content.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS practice_problems (
    id          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title       TEXT        NOT NULL,
    title_slug  TEXT        NOT NULL UNIQUE,
    difficulty  TEXT        NOT NULL,            -- 'easy' | 'medium' | 'hard'
    description TEXT        NOT NULL,
    topic_tags  JSONB,                            -- e.g. ["array", "hash-table"]
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_practice_problems_difficulty ON practice_problems (difficulty);
CREATE INDEX IF NOT EXISTS idx_practice_problems_title_slug ON practice_problems (title_slug);

-- Practice import fix -- 2026-08-19: the importer's slugify gave every
-- non-alphanumeric its own dash, so "Pow(x, n)" landed as "pow-x--n" instead
-- of "pow-x-n". Those don't match leetcode.com/problems/<slug>, and title_slug
-- is the importer's dedup key, so a re-import would have duplicated the 25
-- affected rows rather than skipping them. Collapse the runs; verified
-- collision-free against the 1825-row import, so the UNIQUE index holds.
UPDATE practice_problems
SET    title_slug = trim(both '-' from regexp_replace(title_slug, '-+', '-', 'g'))
WHERE  title_slug LIKE '%--%';

-- Practice import fix -- 2026-08-19: LeetCode's database problems ship in the
-- Kaggle dataset with the literal string "SQL Schema" where the problem
-- statement should be (the real prompt is an image on leetcode.com and never
-- made it into the CSV), which renders as a blank practice card. Drops 156 of
-- 1825 rows. practice_attempts cascades from here, but no attempt referenced
-- one of these. The importer now rejects them at read time
-- (PLACEHOLDER_DESC_LEN), so a re-import won't reintroduce them.
DELETE FROM practice_problems
WHERE  length(btrim(description)) < 50;

-- ---------------------------------------------------------------------------
-- practice_attempts
-- One row per problem a student starts. Created on "Start" (which is when
-- the timer begins -- started_at is the timer's source of truth, not a
-- frontend counter, so a page refresh can't reset or fake it), then
-- updated on submit with the student's code and Gemini's verdict.
-- Feeds the Code Studio dashboard.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS practice_attempts (
    id                 TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id            TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    problem_id         TEXT        NOT NULL REFERENCES practice_problems (id) ON DELETE CASCADE,
    folder_id          TEXT        REFERENCES code_workspace_folders (id) ON DELETE SET NULL,
    language           TEXT,
    submitted_code     TEXT,
    status             TEXT        NOT NULL DEFAULT 'in_progress',  -- in_progress | submitted | abandoned
    is_correct         BOOLEAN,
    feedback           TEXT,
    time_complexity    TEXT,       -- Gemini's estimate, e.g. "O(n log n)"
    space_complexity   TEXT,
    seconds_taken      INTEGER,
    started_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_practice_attempts_user_id ON practice_attempts (user_id);
CREATE INDEX IF NOT EXISTS idx_practice_attempts_problem_id ON practice_attempts (problem_id);
CREATE INDEX IF NOT EXISTS idx_practice_attempts_started_at ON practice_attempts (started_at);
-- ---------------------------------------------------------------------------
-- quizzes  (Module 3 Feature 7 – Amiyo)
-- One row per quiz a student generates. Linked to a chapter (which acts as
-- the topic). attempt_number tracks retakes so Feature 8 can show history.
-- answers is a JSONB list of {question_id, answer_text} written on submit.
-- status flow: not_started → in_progress → submitted | auto_submitted
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quizzes (
    id                 TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id            TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    chapter_id         TEXT        NOT NULL REFERENCES chapters (id) ON DELETE CASCADE,
    title              TEXT        NOT NULL,
    difficulty         TEXT        NOT NULL,
    num_questions      INTEGER     NOT NULL,
    duration_minutes   INTEGER     NOT NULL,
    attempt_number     INTEGER     NOT NULL DEFAULT 1,
    status             TEXT        NOT NULL DEFAULT 'not_started',
    answers            JSONB,
    started_at         TIMESTAMPTZ,
    ends_at            TIMESTAMPTZ,
    submitted_at       TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON quizzes (user_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_chapter_id ON quizzes (chapter_id);

-- ---------------------------------------------------------------------------
-- quiz_questions  (Module 3 Feature 7 – Amiyo)
-- One row per question Gemini generates for a quiz. Deleted automatically
-- when the parent quiz is deleted (ON DELETE CASCADE).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quiz_questions (
    id            TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::text,
    quiz_id       TEXT    NOT NULL REFERENCES quizzes (id) ON DELETE CASCADE,
    question_text TEXT    NOT NULL,
    marks         INTEGER NOT NULL,
    difficulty    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz_id ON quiz_questions (quiz_id);

-- ---------------------------------------------------------------------------
-- Feature 8 grading columns on quizzes  (Module 3 Feature 8 – Amiyo)
-- Added separately so the schema is safe to re-run (IF NOT EXISTS).
-- graded_answers stores [{question_id, question_text, answer_text,
--   marks_obtained, max_marks, feedback}] so the results page needs only
-- one query rather than a JOIN.
-- ---------------------------------------------------------------------------
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS total_score    INTEGER;
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS max_score      INTEGER;
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS percentage     DOUBLE PRECISION;
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS pass_status    TEXT;
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS graded_answers JSONB;
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS graded_at      TIMESTAMPTZ;

-- Feature 7 marks range (replaces marks_per_question)
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS min_marks INTEGER;
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS max_marks INTEGER;

-- Feature 7 note-based generation (each quiz is now tied to a specific note)
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS note_id TEXT REFERENCES notes(id) ON DELETE SET NULL;
ALTER TABLE quizzes DROP COLUMN IF EXISTS marks_per_question;
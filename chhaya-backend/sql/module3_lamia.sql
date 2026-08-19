-- ===========================================================================
-- Module 3, Lamia -- Feature 1 (Voice Narration) + Feature 2 (Concept Map Game)
--
-- MERGE INSTRUCTIONS: append this whole file to the end of your existing
-- chhaya-backend/sql/schema.sql, then re-run schema.sql against your
-- database. Every statement is IF NOT EXISTS, so re-running is safe and
-- nothing already in your database is touched.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- voice_narrations
-- One row per generated narration. A narration belongs to EITHER a note
-- (note_id set, teacher_profile_id optionally set -- the user picks a
-- voice) OR a study guide (study_guide_id set, teacher_profile_id always
-- NULL because the guide was already generated in a teacher's style and
-- the narration inherits that same profile rather than letting the user
-- pick a conflicting one). The CHECK constraint enforces exactly one
-- source, so a malformed row can't reach the application layer.
--
-- audio_path follows the same convention as notes.file_path and
-- exam_papers.file_path: stored on disk, served through its own
-- /voice-narrations/{id}/audio endpoint rather than exposed as a path.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS voice_narrations (
    id                 TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id            TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    note_id            TEXT        REFERENCES notes (id) ON DELETE CASCADE,
    study_guide_id     TEXT        REFERENCES study_guides (id) ON DELETE CASCADE,
    teacher_profile_id TEXT        REFERENCES teacher_profiles (id) ON DELETE SET NULL,
    voice_short_name   TEXT,       -- the Edge TTS voice actually used, e.g. 'en-US-GuyNeural'
    rate               TEXT,       -- SSML-style rate applied to match the teacher's pacing, e.g. '-10%'
    status             TEXT        NOT NULL DEFAULT 'pending',
    error_message      TEXT,
    audio_path         TEXT,
    duration_seconds   INTEGER,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT voice_narration_has_exactly_one_source CHECK (
        (note_id IS NOT NULL AND study_guide_id IS NULL)
        OR (note_id IS NULL AND study_guide_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_voice_narrations_user_id ON voice_narrations (user_id);
CREATE INDEX IF NOT EXISTS idx_voice_narrations_note_id ON voice_narrations (note_id);
CREATE INDEX IF NOT EXISTS idx_voice_narrations_study_guide_id ON voice_narrations (study_guide_id);

-- ---------------------------------------------------------------------------
-- concept_maps
-- The extracted node/edge graph behind the concept-map recall game.
-- `nodes` and `edges` are JSONB in the unified shape the frontend game
-- board parses directly (see app/utils/concept_extractor.py for how they
-- are built, and the frontend's ConceptMapGame.jsx for how they render).
--
-- source_kind records WHICH extractor produced this map ('text' via NLTK,
-- 'code' via Python's ast, 'math' via regex) -- useful both for debugging
-- a bad extraction and for the UI to label what kind of puzzle this is.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS concept_maps (
    id            TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       TEXT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title         TEXT        NOT NULL,
    source_kind   TEXT        NOT NULL,   -- 'text' | 'code' | 'math'
    source_text   TEXT        NOT NULL,
    nodes         JSONB       NOT NULL,
    edges         JSONB       NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_concept_maps_user_id ON concept_maps (user_id);

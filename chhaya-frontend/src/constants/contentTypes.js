/*
  Mirrors app/models/annotation.py's ContentType constants on the backend
  -- kept in one place on the frontend too so "study_guide" / "note"
  never gets typo'd differently across the pages that use them
  (GuideDetailPage.jsx, NoteViewerPage.jsx).
*/
export const ContentType = {
  STUDY_GUIDE: "study_guide",
  NOTE: "note",
};

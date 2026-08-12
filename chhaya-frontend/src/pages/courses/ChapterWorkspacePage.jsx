import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import Badge from "../../components/ui/Badge";
import { getChapter, getChapterContents, renameChapter, deleteChapter } from "../../api/courses";
import { createNote, deleteNote } from "../../api/notes";
import { listGlossary, deleteGlossaryEntry } from "../../api/glossary";
import { listStudyGuides, fileStudyGuide, unfileStudyGuide } from "../../api/studyGuides";

/*
  Module 2 (Lamia) -- the Chapter Workspace: the "coherent structure"
  described in the feature spec, where a student sees every piece of
  content filed under one chapter (study guides + uploaded notes) plus
  that chapter's saved glossary, all in one place. This is the busiest
  Module 2 page because it's the hub everything else (annotation,
  glossary, note viewing) branches off from -- same role
  StyleLibraryPage.jsx plays for teaching-style profiles, one level up
  in complexity since it's aggregating three kinds of content at once.
*/

export default function ChapterWorkspacePage() {
  const { courseId, chapterId } = useParams();
  const navigate = useNavigate();
  const [contents, setContents] = useState(null); // {chapter, study_guides, notes}
  const [glossary, setGlossary] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [deletingChapter, setDeletingChapter] = useState(false);
  const [deletingNote, setDeletingNote] = useState(null);
  const [filingGuide, setFilingGuide] = useState(false);

  const refresh = () => {
    getChapterContents(chapterId).then(setContents);
    listGlossary(chapterId).then(setGlossary);
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapterId]);

  async function handleRename() {
    if (!renameValue.trim()) return;
    await renameChapter(chapterId, renameValue.trim());
    setRenaming(false);
    refresh();
  }

  async function handleDeleteChapter() {
    await deleteChapter(chapterId);
    navigate(`/courses/${courseId}`);
  }

  async function handleDeleteNote() {
    if (!deletingNote) return;
    await deleteNote(deletingNote.id);
    setDeletingNote(null);
    refresh();
  }

  if (contents === null || glossary === null) {
    return (
      <AppShell section="Courses" current="Loading...">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  const { chapter, study_guides: guides, notes } = contents;

  return (
    <AppShell section="Courses" current={chapter.title}>
      <div className="page-head">
        <div>
          <Link to={`/courses/${courseId}`} className="hint" style={{ marginBottom: 4, display: "inline-block" }}>&larr; Back to course</Link>
          <div className="page-title">{chapter.title}</div>
          <div className="page-sub">
            {guides.length} study guide{guides.length === 1 ? "" : "s"} · {notes.length} note{notes.length === 1 ? "" : "s"} · {glossary.length} glossary word{glossary.length === 1 ? "" : "s"}
          </div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" icon={<Icon name="fileText" size={16} />} onClick={() => { setRenaming(true); setRenameValue(chapter.title); }}>Rename</Button>
          <Button variant="danger" icon={<Icon name="trash" size={16} />} onClick={() => setDeletingChapter(true)}>Delete</Button>
        </div>
      </div>

      <div className="workspace-grid">
        <div className="workspace-main">
          {/* ---- Study guides filed here ---- */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-head">
              <span className="card-title">Study guides</span>
              <div style={{ display: "flex", gap: 12 }}>
                <button className="card-note" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--primary-dark)" }} onClick={() => setFilingGuide(true)}>+ Add existing</button>
                <Link to="/guides/new" className="card-note">+ Generate new</Link>
              </div>
            </div>
            {guides.length === 0 ? (
              <div className="card-pad hint">None filed here yet. Click "Add existing" to file a previously generated study guide, or "Generate new" to create one.</div>
            ) : (
              guides.map((g) => (
                <div key={g.id} className="prow">
                  <Icon name="guides" size={16} />
                  <Link to={`/courses/${courseId}/chapters/${chapterId}/guides/${g.id}`} className="prow-id" style={{ flex: 1, textDecoration: "none", color: "inherit" }}>
                    <div className="prow-name">{g.topic}</div>
                  </Link>
                  <Badge variant={g.status === "ready" ? "ok" : g.status === "failed" ? "danger" : "amber"}>{g.status}</Badge>
                  <div className="prow-act">
                    <button className="mini-btn" onClick={() => unfileStudyGuide(g.id).then(refresh)} title="Remove from chapter">
                      <Icon name="trash" size={15} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* ---- Uploaded notes ---- */}
          <div className="card">
            <div className="card-head">
              <span className="card-title">Your notes</span>
              <button className="card-note" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--primary-dark)" }} onClick={() => setUploading(true)}>
                + Upload a note
              </button>
            </div>
            {notes.length === 0 ? (
              <div className="card-pad hint">No personal notes uploaded to this chapter yet. Add text, an image, or a PDF.</div>
            ) : (
              notes.map((n) => (
                <div key={n.id} className="prow">
                  <Icon name={n.note_type === "text" ? "fileText" : "exams"} size={16} />
                  <div className="prow-id" style={{ flex: 1, cursor: "pointer" }} onClick={() => navigate(`/courses/${courseId}/chapters/${chapterId}/notes/${n.id}`)}>
                    <div className="prow-name">{n.title}</div>
                  </div>
                  <Badge variant="iris">{n.note_type}</Badge>
                  <div className="prow-act">
                    <button className="mini-btn" onClick={() => setDeletingNote(n)} title="Delete"><Icon name="trash" size={15} /></button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="workspace-side">
          {/* ---- Glossary ---- */}
          <div className="card">
            <div className="card-head">
              <span className="card-title">Glossary</span>
              <span className="card-note">{glossary.length} word{glossary.length === 1 ? "" : "s"}</span>
            </div>
            {glossary.length === 0 ? (
              <div className="card-pad hint">
                Select any word inside a study guide or note and choose "Define" to look it up and save it here.
              </div>
            ) : (
              glossary.map((entry) => (
                <div key={entry.id} className="glossary-row">
                  <div>
                    <div className="glossary-term">{entry.term} {entry.part_of_speech && <span className="hint">({entry.part_of_speech})</span>}</div>
                    <div className="glossary-def">{entry.definition}</div>
                  </div>
                  <button className="mini-btn" onClick={() => deleteGlossaryEntry(entry.id).then(refresh)} title="Remove">
                    <Icon name="trash" size={13} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {uploading && (
        <UploadNoteDialog chapterId={chapterId} onClose={() => setUploading(false)} onSaved={() => { setUploading(false); refresh(); }} />
      )}

      {renaming && (
        <div className="overlay" onClick={() => setRenaming(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-primary"><Icon name="fileText" size={20} /></div>
              <div className="dialog-title">Rename chapter</div>
              <div className="field" style={{ marginTop: 14 }}>
                <div className="input">
                  <input autoFocus value={renameValue} onChange={(e) => setRenameValue(e.target.value)}
                    style={{ border: "none", outline: "none", background: "transparent", flex: 1 }} />
                </div>
              </div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setRenaming(false)}>Cancel</Button>
              <Button onClick={handleRename} disabled={!renameValue.trim()}>Save</Button>
            </div>
          </div>
        </div>
      )}

      {deletingChapter && (
        <div className="overlay" onClick={() => setDeletingChapter(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-danger"><Icon name="trash" size={20} /></div>
              <div className="dialog-title">Delete "{chapter.title}"?</div>
              <div className="dialog-copy">Notes, highlights, sticky notes, and glossary words here are deleted too. Study guides are kept, just unfiled. This can't be undone.</div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setDeletingChapter(false)}>Keep chapter</Button>
              <Button variant="danger" onClick={handleDeleteChapter}>Delete chapter</Button>
            </div>
          </div>
        </div>
      )}

      {deletingNote && (
        <div className="overlay" onClick={() => setDeletingNote(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-danger"><Icon name="trash" size={20} /></div>
              <div className="dialog-title">Delete "{deletingNote.title}"?</div>
              <div className="dialog-copy">This can't be undone.</div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setDeletingNote(null)}>Keep note</Button>
              <Button variant="danger" onClick={handleDeleteNote}>Delete note</Button>
            </div>
          </div>
        </div>
      )}
      {filingGuide && (
        <FileGuideDialog chapterId={chapterId} onClose={() => setFilingGuide(false)} onFiled={() => { setFilingGuide(false); refresh(); }} />
      )}
    </AppShell>
  );
}

function UploadNoteDialog({ chapterId, onClose, onSaved }) {
  const [title, setTitle] = useState("");
  const [noteType, setNoteType] = useState("text");
  const [textContent, setTextContent] = useState("");
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSave() {
    if (!title.trim()) { setError("Give the note a title."); return; }
    if (noteType === "text" && !textContent.trim()) { setError("Write something, or switch to Image/PDF."); return; }
    if (noteType !== "text" && !file) { setError("Choose a file to upload."); return; }

    setSaving(true);
    setError("");
    try {
      await createNote({ chapterId, title: title.trim(), noteType, textContent, file });
      onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save that note.");
      setSaving(false);
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="dialog" style={{ width: 480 }} onClick={(e) => e.stopPropagation()}>
        <div className="dialog-pad">
          <div className="dialog-icon di-primary"><Icon name="fileText" size={20} /></div>
          <div className="dialog-title">Upload a note</div>

          <div className="field" style={{ marginTop: 14 }}>
            <div className="label">Title</div>
            <div className="input">
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Lecture 3 notes"
                style={{ border: "none", outline: "none", background: "transparent", flex: 1 }} />
            </div>
          </div>

          <div className="field" style={{ marginTop: 12 }}>
            <div className="label">Type</div>
            <div style={{ display: "flex", gap: 8 }}>
              {["text", "image", "pdf"].map((t) => (
                <button key={t} type="button" className={`chip ${noteType === t ? "chip-on" : ""}`} onClick={() => setNoteType(t)}>
                  {t === "text" ? "Text" : t === "image" ? "Image" : "PDF"}
                </button>
              ))}
            </div>
          </div>

          {noteType === "text" ? (
            <div className="field" style={{ marginTop: 12 }}>
              <div className="label">Content</div>
              <textarea className="annot-sticky-textarea" style={{ minHeight: 140 }} value={textContent}
                onChange={(e) => setTextContent(e.target.value)} placeholder="Type or paste your notes here..." />
            </div>
          ) : (
            <div className="field" style={{ marginTop: 12 }}>
              <div className="label">File</div>
              <div className="upload-drop">
                <input type="file" accept={noteType === "pdf" ? ".pdf,application/pdf" : "image/*"} onChange={(e) => setFile(e.target.files?.[0] || null)} />
                <div className="hint">{noteType === "pdf" ? "PDF files." : "JPG or PNG files."}</div>
              </div>
            </div>
          )}

          {error && <div className="error-text" style={{ marginTop: 8 }}>{error}</div>}
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>{saving ? "Saving..." : "Save note"}</Button>
        </div>
      </div>
    </div>
  );
}

function FileGuideDialog({ chapterId, onClose, onFiled }) {
  const [allGuides, setAllGuides] = useState(null);
  const [filing, setFiling] = useState(null);

  useEffect(() => {
    listStudyGuides().then(setAllGuides);
  }, []);

  // Show only guides that are "ready" and not already filed into any chapter
  const available = allGuides?.filter((g) => g.status === "ready" && !g.chapter_id) || [];

  async function handleFile(guideId) {
    setFiling(guideId);
    await fileStudyGuide(guideId, chapterId);
    onFiled();
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="dialog" style={{ width: 520 }} onClick={(e) => e.stopPropagation()}>
        <div className="dialog-pad">
          <div className="dialog-icon di-primary"><Icon name="guides" size={20} /></div>
          <div className="dialog-title">Add existing study guide</div>
          <div className="dialog-copy">Pick a completed study guide to file into this chapter.</div>

          <div style={{ marginTop: 14, maxHeight: 320, overflowY: "auto" }}>
            {allGuides === null ? (
              <div className="hint" style={{ padding: "12px 0" }}>Loading your study guides...</div>
            ) : available.length === 0 ? (
              <div className="hint" style={{ padding: "12px 0" }}>No unfiled study guides available. Generate one first from the <a href="/guides/new" style={{ color: "var(--primary-dark)" }}>Study Guides</a> page.</div>
            ) : (
              available.map((g) => (
                <div key={g.id} className="prow" style={{ cursor: "pointer" }} onClick={() => handleFile(g.id)}>
                  <Icon name="guides" size={16} />
                  <div className="prow-id" style={{ flex: 1 }}>
                    <div className="prow-name">{g.topic}</div>
                  </div>
                  {filing === g.id ? (
                    <span className="hint" style={{ fontSize: 12 }}>Filing...</span>
                  ) : (
                    <Badge variant="ok">ready</Badge>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
        </div>
      </div>
    </div>
  );
}

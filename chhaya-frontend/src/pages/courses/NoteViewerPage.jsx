import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import Badge from "../../components/ui/Badge";
import AnnotatableText, { HighlightableText } from "../../components/annotations/AnnotatableText";
import { getNote, updateNote, getNoteFileBlob } from "../../api/notes";
import { getChapter } from "../../api/courses";
import { ContentType } from "../../constants/contentTypes";

/*
  Module 2 (Lamia) -- viewing (and, for text notes, editing) one uploaded
  note, wrapped in AnnotatableText so the same highlight / sticky note /
  word-lookup toolbar that works on a study guide also works here -- the
  spec asks for annotation on "a generated guide, an uploaded note, a
  formula sheet" uniformly, and this is the uploaded-note half of that.
*/

export default function NoteViewerPage() {
  const { courseId, chapterId, noteId } = useParams();
  const [note, setNote] = useState(null);
  const [chapter, setChapter] = useState(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [fileUrl, setFileUrl] = useState(null);

  useEffect(() => {
    getNote(noteId).then(setNote);
    getChapter(chapterId).then(setChapter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [noteId, chapterId]);

  useEffect(() => {
    if (note && note.note_type !== "text") {
      getNoteFileBlob(note.id).then((blob) => setFileUrl(URL.createObjectURL(blob)));
    }
  }, [note]);

  async function handleSave() {
    const updated = await updateNote(noteId, { textContent: draft });
    setNote(updated);
    setEditing(false);
  }

  if (!note || !chapter) {
    return (
      <AppShell section="Courses" current="Loading...">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Courses" current={note.title}>
      <div className="page-head">
        <div>
          <Link to={`/courses/${courseId}/chapters/${chapterId}`} className="hint" style={{ marginBottom: 4, display: "inline-block" }}>
            &larr; Back to {chapter.title}
          </Link>
          <div className="page-title">{note.title}</div>
          <div className="page-sub"><Badge variant="iris">{note.note_type}</Badge></div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" icon={<Icon name="fileText" size={16} />} onClick={() => window.print()}>
            Export to PDF
          </Button>
          {note.note_type === "text" && !editing && (
            <Button variant="ghost" icon={<Icon name="fileText" size={16} />} onClick={() => { setDraft(note.text_content || ""); setEditing(true); }}>
              Edit
            </Button>
          )}
        </div>
      </div>

      <div className="card card-pad">
        {note.note_type === "text" ? (
          editing ? (
            <>
              <textarea className="annot-sticky-textarea" style={{ minHeight: 260, width: "100%" }} value={draft} onChange={(e) => setDraft(e.target.value)} autoFocus />
              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <Button onClick={handleSave}>Save</Button>
                <Button variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </>
          ) : (
            <AnnotatableText chapterId={chapterId} contentType={ContentType.NOTE} contentId={note.id} topic={note.title}>
              <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6, fontSize: 14 }}>
                <HighlightableText>{note.text_content}</HighlightableText>
              </div>
            </AnnotatableText>
          )
        ) : note.note_type === "image" ? (
          <AnnotatableText chapterId={chapterId} contentType={ContentType.NOTE} contentId={note.id} topic={note.title}>
            {fileUrl ? <img src={fileUrl} alt={note.title} style={{ maxWidth: "100%", borderRadius: 8 }} /> : <div className="hint">Loading image...</div>}
          </AnnotatableText>
        ) : (
          <AnnotatableText chapterId={chapterId} contentType={ContentType.NOTE} contentId={note.id} topic={note.title}>
            {fileUrl ? (
              <a className="btn btn-primary" href={fileUrl} target="_blank" rel="noreferrer">
                <Icon name="fileText" size={16} /> Open PDF
              </a>
            ) : (
              <div className="hint">Loading file...</div>
            )}
          </AnnotatableText>
        )}
      </div>
    </AppShell>
  );
}

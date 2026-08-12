import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { getCourse, listChapters, createChapter, renameChapter, deleteChapter, reorderChapters } from "../../api/courses";

/*
  Module 2 (Lamia) -- Chapters within one Course. Same CRUD+reorder shape
  as CoursesListPage.jsx one level down the tree (Course -> Chapter),
  matching the folder/subfolder organization described in the feature
  spec (Apple Notes / Evernote / OneNote style nesting).
*/

export default function CourseDetailPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [chapters, setChapters] = useState(null);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [renaming, setRenaming] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const [deleting, setDeleting] = useState(null);

  const refresh = () => {
    getCourse(courseId).then(setCourse);
    listChapters(courseId).then(setChapters);
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  async function handleCreate() {
    if (!newTitle.trim()) return;
    await createChapter(courseId, newTitle.trim());
    setNewTitle("");
    setCreating(false);
    refresh();
  }

  async function handleRename() {
    if (!renameValue.trim() || !renaming) return;
    await renameChapter(renaming.id, renameValue.trim());
    setRenaming(null);
    refresh();
  }

  async function handleDelete() {
    if (!deleting) return;
    await deleteChapter(deleting.id);
    setDeleting(null);
    refresh();
  }

  async function move(chapter, direction) {
    if (!chapters) return;
    const index = chapters.findIndex((c) => c.id === chapter.id);
    const swapWith = index + direction;
    if (swapWith < 0 || swapWith >= chapters.length) return;
    const reordered = [...chapters];
    [reordered[index], reordered[swapWith]] = [reordered[swapWith], reordered[index]];
    setChapters(reordered);
    await reorderChapters(courseId, reordered.map((c) => c.id));
    refresh();
  }

  if (course === null || chapters === null) {
    return (
      <AppShell section="Courses" current="Loading...">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Courses" current={course.title}>
      <div className="page-head">
        <div>
          <Link to="/courses" className="hint" style={{ marginBottom: 4, display: "inline-block" }}>&larr; All courses</Link>
          <div className="page-title">{course.title}</div>
          <div className="page-sub">
            {chapters.length === 0 ? "Add a chapter to start filing content here." : `${chapters.length} chapter${chapters.length === 1 ? "" : "s"}.`}
          </div>
        </div>
        <div className="page-actions">
          <Button icon={<Icon name="plus" size={16} />} onClick={() => setCreating(true)}>New chapter</Button>
        </div>
      </div>

      {chapters.length === 0 ? (
        <div className="list-card">
          <div className="lib-empty">
            <div className="lib-empty-title">No chapters yet</div>
            <div className="lib-empty-copy">
              A chapter is where study guides, uploaded notes, highlights, and glossary words for one part of the
              syllabus live together -- e.g. "Chapter 1: Complexity Analysis".
            </div>
            <Button icon={<Icon name="plus" size={16} />} onClick={() => setCreating(true)}>Add your first chapter</Button>
          </div>
        </div>
      ) : (
        <div className="list-card">
          {chapters.map((chapter, i) => (
            <div key={chapter.id} className="prow" onClick={() => navigate(`/courses/${courseId}/chapters/${chapter.id}`)} style={{ cursor: "pointer" }}>
              <div className="reorder-cell" onClick={(e) => e.stopPropagation()}>
                <button className="mini-btn" disabled={i === 0} onClick={() => move(chapter, -1)} title="Move up">
                  <Icon name="chevronDown" size={13} style={{ transform: "rotate(180deg)" }} />
                </button>
                <button className="mini-btn" disabled={i === chapters.length - 1} onClick={() => move(chapter, 1)} title="Move down">
                  <Icon name="chevronDown" size={13} />
                </button>
              </div>
              <Icon name="guides" size={16} />
              <div className="prow-id" style={{ flex: 1 }}>
                <div className="prow-name">{chapter.title}</div>
              </div>
              <div className="prow-act" onClick={(e) => e.stopPropagation()}>
                <button className="mini-btn" onClick={() => { setRenaming(chapter); setRenameValue(chapter.title); }} title="Rename">
                  <Icon name="fileText" size={15} />
                </button>
                <button className="mini-btn" onClick={() => setDeleting(chapter)} title="Delete">
                  <Icon name="trash" size={15} />
                </button>
                <Icon name="chevronRight" size={15} />
              </div>
            </div>
          ))}
        </div>
      )}

      {creating && (
        <div className="overlay" onClick={() => setCreating(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-primary"><Icon name="plus" size={20} /></div>
              <div className="dialog-title">New chapter</div>
              <div className="field" style={{ marginTop: 14 }}>
                <div className="input">
                  <input autoFocus placeholder="e.g. Chapter 1" value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                    style={{ border: "none", outline: "none", background: "transparent", flex: 1 }} />
                </div>
              </div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setCreating(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={!newTitle.trim()}>Create</Button>
            </div>
          </div>
        </div>
      )}

      {renaming && (
        <div className="overlay" onClick={() => setRenaming(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-primary"><Icon name="fileText" size={20} /></div>
              <div className="dialog-title">Rename chapter</div>
              <div className="field" style={{ marginTop: 14 }}>
                <div className="input">
                  <input autoFocus value={renameValue} onChange={(e) => setRenameValue(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleRename()}
                    style={{ border: "none", outline: "none", background: "transparent", flex: 1 }} />
                </div>
              </div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setRenaming(null)}>Cancel</Button>
              <Button onClick={handleRename} disabled={!renameValue.trim()}>Save</Button>
            </div>
          </div>
        </div>
      )}

      {deleting && (
        <div className="overlay" onClick={() => setDeleting(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-danger"><Icon name="trash" size={20} /></div>
              <div className="dialog-title">Delete "{deleting.title}"?</div>
              <div className="dialog-copy">
                Every note, highlight, sticky note, and glossary entry filed here is deleted too. Study guides
                filed here are kept, just unfiled. This can't be undone.
              </div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setDeleting(null)}>Keep chapter</Button>
              <Button variant="danger" onClick={handleDelete}>Delete chapter</Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

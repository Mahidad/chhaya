import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { listCourses, createCourse, renameCourse, deleteCourse, reorderCourses } from "../../api/courses";

/*
  Module 2 (Lamia) -- Course & Chapter Organization, top level. Built as
  the same worked pattern as StyleLibraryPage.jsx (Mahidad's Feature 3):
  fetch on mount, render list-or-empty, call an API function on user
  action. Reordering is up/down buttons rather than drag-and-drop -- no
  drag-and-drop library is used anywhere else in this codebase, and
  buttons are enough to exercise the real PATCH /courses/reorder endpoint
  without adding a new dependency for one feature.
*/

export default function CoursesListPage() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState(null); // null = loading
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [renaming, setRenaming] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const [deleting, setDeleting] = useState(null);

  const refresh = () => listCourses().then(setCourses);

  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate() {
    if (!newTitle.trim()) return;
    await createCourse(newTitle.trim());
    setNewTitle("");
    setCreating(false);
    refresh();
  }

  async function handleRename() {
    if (!renameValue.trim() || !renaming) return;
    await renameCourse(renaming.id, renameValue.trim());
    setRenaming(null);
    refresh();
  }

  async function handleDelete() {
    if (!deleting) return;
    await deleteCourse(deleting.id);
    setDeleting(null);
    refresh();
  }

  async function move(course, direction) {
    if (!courses) return;
    const index = courses.findIndex((c) => c.id === course.id);
    const swapWith = index + direction;
    if (swapWith < 0 || swapWith >= courses.length) return;
    const reordered = [...courses];
    [reordered[index], reordered[swapWith]] = [reordered[swapWith], reordered[index]];
    setCourses(reordered); // optimistic
    await reorderCourses(reordered.map((c) => c.id));
    refresh();
  }

  if (courses === null) {
    return (
      <AppShell section="Courses" current="All courses">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Courses" current="All courses">
      <div className="page-head">
        <div>
          <div className="page-title">Courses</div>
          <div className="page-sub">
            {courses.length === 0
              ? "Create a course to start organizing your study guides and notes."
              : `${courses.length} course${courses.length === 1 ? "" : "s"}.`}
          </div>
        </div>
        <div className="page-actions">
          <Button icon={<Icon name="plus" size={16} />} onClick={() => setCreating(true)}>New course</Button>
        </div>
      </div>

      {courses.length === 0 ? (
        <div className="list-card">
          <div className="lib-empty">
            <div className="lib-empty-title">No courses yet</div>
            <div className="lib-empty-copy">
              A course is a container for chapters -- e.g. "CSE461" -- and chapters hold your study guides,
              uploaded notes, highlights, and glossary for that part of the syllabus.
            </div>
            <Button icon={<Icon name="plus" size={16} />} onClick={() => setCreating(true)}>Create your first course</Button>
          </div>
        </div>
      ) : (
        <div className="list-card">
          {courses.map((course, i) => (
            <div key={course.id} className="prow" onClick={() => navigate(`/courses/${course.id}`)} style={{ cursor: "pointer" }}>
              <div className="reorder-cell" onClick={(e) => e.stopPropagation()}>
                <button className="mini-btn" disabled={i === 0} onClick={() => move(course, -1)} title="Move up">
                  <Icon name="chevronDown" size={13} style={{ transform: "rotate(180deg)" }} />
                </button>
                <button className="mini-btn" disabled={i === courses.length - 1} onClick={() => move(course, 1)} title="Move down">
                  <Icon name="chevronDown" size={13} />
                </button>
              </div>
              <div className="avatar">{course.title.slice(0, 2).toUpperCase()}</div>
              <div className="prow-id" style={{ flex: 1 }}>
                <div className="prow-name">{course.title}</div>
              </div>
              <div className="prow-act" onClick={(e) => e.stopPropagation()}>
                <button className="mini-btn" onClick={() => { setRenaming(course); setRenameValue(course.title); }} title="Rename">
                  <Icon name="fileText" size={15} />
                </button>
                <button className="mini-btn" onClick={() => setDeleting(course)} title="Delete">
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
              <div className="dialog-title">New course</div>
              <div className="field" style={{ marginTop: 14 }}>
                <div className="input">
                  <input autoFocus placeholder="e.g. CSE461" value={newTitle}
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
              <div className="dialog-title">Rename course</div>
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
                Every chapter inside -- and every note, highlight, sticky note, and glossary entry filed under
                them -- is deleted too. Study guides filed here are kept, just unfiled. This can't be undone.
              </div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setDeleting(null)}>Keep course</Button>
              <Button variant="danger" onClick={handleDelete}>Delete course</Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

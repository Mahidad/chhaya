import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { TextField } from "../../components/ui/Field";
import { listStudyGuides, deleteStudyGuide, renameStudyGuide } from "../../api/studyGuides";
import { addGuideToSchedule, listReviews } from "../../api/reviewSchedules";

const STATUS_BADGE = {
  pending: { variant: undefined, label: "Pending" },
  generating: { variant: "amber", label: "Generating" },
  ready: { variant: "ok", label: "Ready" },
  failed: { variant: "danger", label: "Failed" },
};

export default function StudyGuidesListPage() {
  const [guides, setGuides] = useState(null);
  const [deletingGuide, setDeletingGuide] = useState(null);
  const [renamingGuide, setRenamingGuide] = useState(null);
  const [addingGuideId, setAddingGuideId] = useState(null);
  const [scheduledGuideIds, setScheduledGuideIds] = useState([]);
  const navigate = useNavigate();

  const refresh = () => listStudyGuides().then(setGuides).catch(() => setGuides([]));

  useEffect(() => {
    refresh();
    listReviews("all")
      .then((reviews) => setScheduledGuideIds(reviews.map((review) => review.study_guide_id)))
      .catch(() => setScheduledGuideIds([]));
  }, []);

  async function handleConfirmDelete() {
    if (!deletingGuide) return;
    await deleteStudyGuide(deletingGuide.id);
    setDeletingGuide(null);
    refresh();
  }

  async function handleConfirmRename(newTopic) {
    if (!renamingGuide) return;
    await renameStudyGuide(renamingGuide.id, newTopic);
    setRenamingGuide(null);
    refresh();
  }

  async function handleAddToSchedule(event, guideId) {
    event.preventDefault();
    event.stopPropagation();
    setAddingGuideId(guideId);
    try {
      await addGuideToSchedule(guideId);
      setScheduledGuideIds((ids) => [...ids, guideId]);
    } finally {
      setAddingGuideId(null);
    }
  }

  if (guides === null) {
    return (
      <AppShell section="Study guides" current="All guides">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Study guides" current="All guides">
      <div className="page-head">
        <div>
          <div className="page-title">Study guides</div>
          <div className="page-sub">
            Pick a topic, pick a teacher's style, and Chhaya writes the chapter — even one your teacher never uploaded.
          </div>
        </div>
        {guides.length > 0 && (
          <div className="page-actions">
            <Button icon={<Icon name="plus" size={16} />} onClick={() => navigate("/guides/new")}>
              New study guide
            </Button>
          </div>
        )}
      </div>

      {guides.length === 0 ? (
        <div className="ingest-empty">
          <div className="shadow-mark">
            <div className="disc disc-back" />
            <div className="disc disc-front"><Icon name="guides" size={22} /></div>
          </div>
          <div className="empty-title">No study guides yet</div>
          <div className="empty-copy">
            A guide is a full written chapter in a teacher's style, with a formula sheet if the topic is STEM.
          </div>
          <div className="empty-actions">
            <Button size="lg" icon={<Icon name="plus" size={16} />} onClick={() => navigate("/guides/new")}>
              Write my first guide
            </Button>
            <Link to="/library" className="btn btn-ghost btn-lg">
              <Icon name="library" size={16} /> Browse style library
            </Link>
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {guides.map((g) => {
            const status = STATUS_BADGE[g.status] || STATUS_BADGE.pending;
            return (
              <Link key={g.id} to={`/guides/${g.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <div className="card card-pad" style={{ height: "100%", display: "flex", flexDirection: "column", position: "relative" }}>
                  <div className="thumb"><Icon name="guides" size={26} /></div>
                  <div className="src-title" style={{ marginTop: 12 }}>{g.topic}</div>
                  <div className="src-meta" style={{ marginTop: 8 }}>
                    <Badge variant={status.variant}>{status.label}</Badge>
                    <span style={{ textTransform: "capitalize" }}>{g.depth}</span>
                  </div>
                  <div style={{ marginTop: "auto", paddingTop: 12, display: "flex", gap: 8, justifyContent: "flex-end", borderTop: "1px solid var(--line-soft)" }}>
                    {g.status === "ready" && (
                      <Button
                        size="sm"
                        variant="primary"
                        disabled={addingGuideId === g.id || scheduledGuideIds.includes(g.id)}
                        onClick={(event) => handleAddToSchedule(event, g.id)}
                      >
                        {scheduledGuideIds.includes(g.id) ? "Added to scheduler" : addingGuideId === g.id ? "Adding..." : "Add to scheduler"}
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setRenamingGuide(g);
                      }}
                    >
                      Rename
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setDeletingGuide(g);
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {deletingGuide && (
        <DeleteDialog
          item={deletingGuide}
          onCancel={() => setDeletingGuide(null)}
          onConfirm={handleConfirmDelete}
        />
      )}

      {renamingGuide && (
        <RenameDialog
          item={renamingGuide}
          onCancel={() => setRenamingGuide(null)}
          onConfirm={handleConfirmRename}
        />
      )}
    </AppShell>
  );
}

function DeleteDialog({ item, onCancel, onConfirm }) {
  const [deleting, setDeleting] = useState(false);

  async function handleConfirm() {
    setDeleting(true);
    await onConfirm();
  }

  return (
    <div className="overlay" onClick={onCancel}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-pad">
          <div className="dialog-icon di-danger">
            <Icon name="trash" size={20} />
          </div>
          <div className="dialog-title">Delete "{item.topic}"?</div>
          <div className="dialog-copy">
            This study guide will be permanently removed. This action cannot be undone.
          </div>
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onCancel}>Keep guide</Button>
          <Button variant="danger" onClick={handleConfirm} disabled={deleting}>
            {deleting ? "Deleting..." : "Delete guide"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function RenameDialog({ item, onCancel, onConfirm }) {
  const [topic, setTopic] = useState(item.topic);
  const [saving, setSaving] = useState(false);

  async function handleSave(e) {
    e.preventDefault();
    if (!topic.trim()) return;
    setSaving(true);
    await onConfirm(topic.trim());
  }

  return (
    <div className="overlay" onClick={onCancel}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <form onSubmit={handleSave}>
          <div className="dialog-pad">
            <div className="dialog-title">Rename study guide</div>
            <div className="dialog-copy" style={{ marginBottom: 12 }}>
              Update the topic of this guide in your collection.
            </div>
            <TextField
              label="Topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="dialog-foot">
            <Button variant="ghost" type="button" onClick={onCancel}>Cancel</Button>
            <Button type="submit" disabled={saving || !topic.trim()}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

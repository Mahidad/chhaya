import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import Icon from "../../components/icons/Icon";
import { TextField } from "../../components/ui/Field";
import { listReferenceSources, deleteReferenceSource, renameReferenceSource } from "../../api/referenceSources";

const STATUS_BADGE = {
  pending: { variant: undefined, label: "Pending" },
  processing: { variant: "amber", label: "Analysing" },
  ready: { variant: "ok", label: "Ready" },
  failed: { variant: "danger", label: "Needs attention" },
};

export default function ReferenceSourcesListPage() {
  const [sources, setSources] = useState(null); // null = loading
  const [deletingSource, setDeletingSource] = useState(null);
  const [renamingSource, setRenamingSource] = useState(null);
  const navigate = useNavigate();

  const refresh = () => listReferenceSources().then(setSources).catch(() => setSources([]));

  useEffect(() => {
    refresh();
  }, []);

  async function handleConfirmDelete() {
    if (!deletingSource) return;
    await deleteReferenceSource(deletingSource.id);
    setDeletingSource(null);
    refresh();
  }

  async function handleConfirmRename(newTitle) {
    if (!renamingSource) return;
    await renameReferenceSource(renamingSource.id, newTitle);
    setRenamingSource(null);
    refresh();
  }

  if (sources === null) {
    return (
      <AppShell section="Reference sources" current="All sources">
        <div className="page-head">
          <div>
            <div className="page-title">Reference sources</div>
          </div>
        </div>
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Reference sources" current="All sources">
      <div className="page-head">
        <div>
          <div className="page-title">Reference sources</div>
          <div className="page-sub">
            Point Chhaya at a teacher you already learn from. It reads their lectures and keeps the style.
          </div>
        </div>
        {sources.length > 0 && (
          <div className="page-actions">
            <Button variant="primary" icon={<Icon name="plus" size={16} />} onClick={() => navigate("/sources/new")}>
              Add reference source
            </Button>
          </div>
        )}
      </div>

      {sources.length === 0 ? (
        <>
          <div className="ingest-empty">
            <div className="shadow-mark">
              <div className="disc disc-back" />
              <div className="disc disc-front">
                <Icon name="sources" size={22} strokeWidth="2" />
              </div>
            </div>
            <div className="empty-title">No reference sources yet</div>
            <div className="empty-copy">
              Paste a YouTube playlist or a course link from a teacher whose explanations already work for you.
              Chhaya pulls the transcripts and turns them into a reusable teaching-style profile.
            </div>
            <div className="empty-actions">
              <Button variant="primary" size="lg" icon={<Icon name="plus" size={16} />} onClick={() => navigate("/sources/new")}>
                Add your first source
              </Button>
              <Button variant="ghost" size="lg">See how style profiles work</Button>
            </div>
          </div>

          <div className="pipeline-row">
            <div className="pipe-card">
              <div className="pipe-num">STEP 1</div>
              <div className="pipe-title">Transcript is pulled and cleaned</div>
              <div className="pipe-copy">Captions come in, filler words and timestamps go out.</div>
              <div className="pipe-api">youtube-transcript-api</div>
            </div>
            <div className="pipe-card">
              <div className="pipe-num">STEP 2</div>
              <div className="pipe-title">Teaching style is analysed</div>
              <div className="pipe-copy">Pacing, vocabulary, analogies, example density, sequencing.</div>
              <div className="pipe-api">Gemini</div>
            </div>
            <div className="pipe-card">
              <div className="pipe-num">STEP 3</div>
              <div className="pipe-title">Profile is stored and reused</div>
              <div className="pipe-copy">Every guide, quiz and concept map can borrow this voice.</div>
              <div className="pipe-api">Style library</div>
            </div>
          </div>
        </>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {sources.map((source) => {
            const status = STATUS_BADGE[source.status] || STATUS_BADGE.pending;
            return (
              <Link key={source.id} to={`/sources/${source.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <Card className="card-pad" style={{ height: "100%", display: "flex", flexDirection: "column", position: "relative" }}>
                  <div className="thumb">
                    <Icon name="sources" size={26} strokeWidth="1.6" />
                  </div>
                  <div className="src-title" style={{ marginTop: 12 }}>{source.title}</div>
                  <div className="src-meta" style={{ marginTop: 8 }}>
                    <Badge variant={status.variant}>{status.label}</Badge>
                    <span>{source.videos?.length || 0} video{(source.videos?.length || 0) === 1 ? "" : "s"}</span>
                  </div>
                  <div style={{ marginTop: "auto", paddingTop: 12, display: "flex", gap: 8, justifyContent: "flex-end", borderTop: "1px solid var(--line-soft)" }}>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setRenamingSource(source);
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
                        setDeletingSource(source);
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      )}

      {deletingSource && (
        <DeleteDialog
          item={deletingSource}
          onCancel={() => setDeletingSource(null)}
          onConfirm={handleConfirmDelete}
        />
      )}

      {renamingSource && (
        <RenameDialog
          item={renamingSource}
          onCancel={() => setRenamingSource(null)}
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
          <div className="dialog-title">Delete "{item.title}"?</div>
          <div className="dialog-copy">
            This reference source and its generated style profile will be removed. This cannot be undone.
          </div>
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onCancel}>Keep source</Button>
          <Button variant="danger" onClick={handleConfirm} disabled={deleting}>
            {deleting ? "Deleting..." : "Delete source"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function RenameDialog({ item, onCancel, onConfirm }) {
  const [title, setTitle] = useState(item.title);
  const [saving, setSaving] = useState(false);

  async function handleSave(e) {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    await onConfirm(title.trim());
  }

  return (
    <div className="overlay" onClick={onCancel}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <form onSubmit={handleSave}>
          <div className="dialog-pad">
            <div className="dialog-title">Rename reference source</div>
            <div className="dialog-copy" style={{ marginBottom: 12 }}>
              Update the name of this source in your collection.
            </div>
            <TextField
              label="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="dialog-foot">
            <Button variant="ghost" type="button" onClick={onCancel}>Cancel</Button>
            <Button type="submit" disabled={saving || !title.trim()}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import {
  listTeacherProfiles,
  updateTeacherProfile,
  deleteTeacherProfile,
} from "../../api/teacherProfiles";

/*
  Feature 3 (Teacher Profile Library CRUD + Favorites) -- built as the
  worked second example of the pattern, after Reference Sources. Compare
  this file to ReferenceSourcesListPage.jsx: same shape (fetch on mount,
  render list-or-empty, call an API function on user action), because the
  pattern is what's reusable, not the specific markup.

  DELIBERATE SIMPLIFICATIONS vs. the mahidad-f2 mockups, so you don't
  mistake a missing feature for a bug:
    - No course/filter sidebar rail, no sort dropdown, no search chips --
      one flat list. The mockup's filtering assumes many more profiles
      than a new user will have; add it back once the library actually
      needs it.
    - "Edit profile" is a rename + favorite toggle only, not the mockup's
      slider-based numeric editor. Sliders that rewrite pacing/analogy
      scores and regenerate a sample paragraph depend on a generation
      endpoint that doesn't exist yet -- that's real scope for later, not
      dropped by accident.
    - The delete-confirm dialog doesn't show "12 guides / 4 concept maps
      use this style" impact numbers, because Study Guides and Concept
      Maps (other teammates' modules) don't exist yet to count.
*/

export default function StyleLibraryPage() {
  const [profiles, setProfiles] = useState(null); // null = loading
  const [renaming, setRenaming] = useState(null); // profile being renamed, or null
  const [deleting, setDeleting] = useState(null); // profile being deleted, or null

  const refresh = () => listTeacherProfiles().then(setProfiles);

  useEffect(() => {
    refresh();
  }, []);

  async function togglePin(profile) {
    // Optimistic update: flip it in the UI immediately, then confirm with
    // the server. Feels instant; if the request fails we just refetch.
    setProfiles((prev) =>
      prev.map((p) => (p.id === profile.id ? { ...p, is_favorite: !p.is_favorite } : p))
    );
    try {
      await updateTeacherProfile(profile.id, { is_favorite: !profile.is_favorite });
    } catch {
      refresh();
    }
  }

  async function confirmDelete() {
    await deleteTeacherProfile(deleting.id);
    setDeleting(null);
    refresh();
  }

  if (profiles === null) {
    return (
      <AppShell section="Style library" current="All profiles">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  const pinned = profiles.filter((p) => p.is_favorite);
  const rest = profiles.filter((p) => !p.is_favorite);

  return (
    <AppShell section="Style library" current="All profiles">
      <div className="page-head">
        <div>
          <div className="page-title">Style library</div>
          <div className="page-sub">
            {profiles.length === 0
              ? "Saved teaching styles will land here."
              : `${profiles.length} saved teaching style${profiles.length === 1 ? "" : "s"}.`}
          </div>
        </div>
      </div>

      {profiles.length === 0 ? (
        <div className="list-card">
          <div className="lib-empty">
            <div className="lib-empty-title">Your library is empty</div>
            <div className="lib-empty-copy">
              A style profile is created after Chhaya reads a reference source. Add a teacher you already
              follow, and their style will be waiting here.
            </div>
            <Link to="/sources/new" className="btn btn-primary">
              <Icon name="sources" size={16} /> Add a reference source
            </Link>
          </div>
        </div>
      ) : (
        <div className="list-card">
          {pinned.length > 0 && (
            <>
              <div className="list-section">
                <Icon name="pin" size={13} /> Pinned
              </div>
              {pinned.map((p) => (
                <ProfileRow key={p.id} profile={p} onTogglePin={togglePin} onRename={setRenaming} onDelete={setDeleting} />
              ))}
            </>
          )}
          <div className="list-section">All profiles</div>
          {rest.map((p) => (
            <ProfileRow key={p.id} profile={p} onTogglePin={togglePin} onRename={setRenaming} onDelete={setDeleting} />
          ))}
        </div>
      )}

      {renaming && (
        <RenameDialog
          profile={renaming}
          onClose={() => setRenaming(null)}
          onSaved={() => {
            setRenaming(null);
            refresh();
          }}
        />
      )}

      {deleting && (
        <DeleteDialog profile={deleting} onCancel={() => setDeleting(null)} onConfirm={confirmDelete} />
      )}
    </AppShell>
  );
}

function ProfileRow({ profile, onTogglePin, onRename, onDelete }) {
  return (
    <div className="prow">
      <span
        className={`pin-cell ${profile.is_favorite ? "pin-on" : ""}`}
        onClick={() => onTogglePin(profile)}
        title={profile.is_favorite ? "Unpin" : "Pin"}
      >
        <Icon name="pin" size={16} />
      </span>
      <div className="avatar">{profile.display_name.slice(0, 2).toUpperCase()}</div>
      <div className="prow-id" style={{ flex: 1 }}>
        <div className="prow-name">{profile.display_name}</div>
      </div>
      <div className="prow-tags">
        {profile.analogy_frequency === "high" && <Badge variant="primary">Analogy-heavy</Badge>}
        {profile.vocabulary_level && <Badge variant="iris">{profile.vocabulary_level}</Badge>}
      </div>
      <div className="prow-act">
        <button className="mini-btn" onClick={() => onRename(profile)} title="Rename">
          <Icon name="fileText" size={15} />
        </button>
        <button className="mini-btn" onClick={() => onDelete(profile)} title="Delete">
          <Icon name="trash" size={15} />
        </button>
      </div>
    </div>
  );
}

function RenameDialog({ profile, onClose, onSaved }) {
  const [name, setName] = useState(profile.display_name);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await updateTeacherProfile(profile.id, { display_name: name });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-pad">
          <div className="dialog-icon di-primary">
            <Icon name="fileText" size={20} />
          </div>
          <div className="dialog-title">Rename profile</div>
          <div className="field" style={{ marginTop: 14 }}>
            <div className="input">
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{ border: "none", outline: "none", background: "transparent", flex: 1 }}
              />
            </div>
          </div>
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving || !name.trim()}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function DeleteDialog({ profile, onCancel, onConfirm }) {
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
          <div className="dialog-title">Delete "{profile.display_name}"?</div>
          <div className="dialog-copy">
            The profile is removed for good. This can't be undone.
          </div>
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onCancel}>Keep profile</Button>
          <Button variant="danger" onClick={handleConfirm} disabled={deleting}>
            {deleting ? "Deleting..." : "Delete profile"}
          </Button>
        </div>
      </div>
    </div>
  );
}

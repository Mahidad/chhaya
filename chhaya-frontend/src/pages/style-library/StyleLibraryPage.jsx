import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import CodingStylesTab from "../../components/style-library/CodingStylesTab";
import {
  listTeacherProfiles,
  updateTeacherProfile,
  deleteTeacherProfile,
  getPreferenceProfile,
} from "../../api/teacherProfiles";

/*
  Feature 3 (Teacher Profile Library CRUD + Favorites) -- built as the
  worked second example of the pattern, after Reference Sources. Compare
  this file to ReferenceSourcesListPage.jsx: same shape (fetch on mount,
  render list-or-empty, call an API function on user action), because the
  pattern is what's reusable, not the specific markup.
*/

export default function StyleLibraryPage() {
  const [tab, setTab] = useState("teaching");
  const [profiles, setProfiles] = useState(null); // null = loading
  const [preference, setPreference] = useState(null);
  const [codingCount, setCodingCount] = useState(0);
  const [renaming, setRenaming] = useState(null); // profile being renamed, or null
  const [deleting, setDeleting] = useState(null); // profile being deleted, or null

  const refresh = () => {
    listTeacherProfiles().then(setProfiles);
    getPreferenceProfile().then(setPreference).catch(() => setPreference(null));
  };

  useEffect(() => {
    refresh();
  }, []);

  async function togglePin(profile) {
    setProfiles((prev) =>
      prev.map((p) => (p.id === profile.id ? { ...p, is_favorite: !p.is_favorite } : p))
    );
    try {
      await updateTeacherProfile(profile.id, { is_favorite: !profile.is_favorite });
      getPreferenceProfile().then(setPreference).catch(() => setPreference(null));
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

  const subtitle =
    tab === "teaching"
      ? profiles.length === 0
        ? "Saved teaching styles will land here."
        : `${profiles.length} saved teaching style${profiles.length === 1 ? "" : "s"}.`
      : codingCount === 0
        ? "Saved coding styles will land here."
        : `${codingCount} saved coding style${codingCount === 1 ? "" : "s"}.`;

  return (
    <AppShell section="Style library" current="All profiles">
      <div className="page-head">
        <div>
          <div className="page-title">Style library</div>
          <div className="page-sub">{subtitle}</div>
        </div>
      </div>

      <TabBar tab={tab} setTab={setTab} />

      {tab === "coding" ? (
        <CodingStylesTab onCountChange={setCodingCount} />
      ) : (
        <>
          {preference && <TeachingPreferenceCard preference={preference} />}

          {profiles.length === 0 ? (
            <div className="list-card">
              <div className="lib-empty">
                <div className="lib-empty-title">Your library is empty</div>
                <div className="lib-empty-copy">
                  A style profile is created after Chhaya reads a reference source. Add a teacher you already
                  follow, and save their style here.
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
        </>
      )}
    </AppShell>
  );
}

function getPacingLabel(score) {
  if (score <= 40) return "Slow pacing";
  if (score <= 70) return "Moderate pacing";
  return "Fast pacing";
}
function getVocabLabel(score) {
  if (score <= 40) return "Beginner vocabulary";
  if (score <= 70) return "Intermediate vocabulary";
  return "Advanced vocabulary";
}
function getAnalogyLabel(score) {
  if (score <= 40) return "Few analogies";
  if (score <= 70) return "Some analogies";
  return "Analogy-heavy";
}
function getExampleLabel(score) {
  if (score <= 40) return "Few examples";
  if (score <= 70) return "Some examples";
  return "Example-rich";
}

function TeachingPreferenceCard({ preference }) {
  if (!preference) return null;

  return (
    <div className="card" style={{ marginBottom: 16, padding: "16px 18px" }}>
      <div className="card-head" style={{ marginBottom: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="sparkles" size={18} style={{ color: "var(--primary)" }} />
          <span className="card-title">Teaching Style Preference Profile</span>
        </div>
        <span className="card-note">Computed from {preference.profile_count} saved style{preference.profile_count === 1 ? "" : "s"}</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>Pacing</div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{Math.round(preference.pacing_score)}% ({getPacingLabel(preference.pacing_score)})</div>
          <div className="meter" style={{ marginTop: 6 }}>
            <div className="meter-fill" style={{ width: `${preference.pacing_score}%` }} />
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>Vocabulary</div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{Math.round(preference.vocabulary_score)}% ({getVocabLabel(preference.vocabulary_score)})</div>
          <div className="meter" style={{ marginTop: 6 }}>
            <div className="meter-fill" style={{ width: `${preference.vocabulary_score}%` }} />
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>Analogies</div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{Math.round(preference.analogy_score)}% ({getAnalogyLabel(preference.analogy_score)})</div>
          <div className="meter" style={{ marginTop: 6 }}>
            <div className="meter-fill meter-amber" style={{ width: `${preference.analogy_score}%` }} />
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>Example Density</div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{Math.round(preference.example_score)}% ({getExampleLabel(preference.example_score)})</div>
          <div className="meter" style={{ marginTop: 6 }}>
            <div className="meter-fill" style={{ width: `${preference.example_score}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}

const PACING_LABEL = { slow: "Slow pacing", moderate: "Moderate pacing", fast: "Fast pacing" };
const VOCAB_LABEL = { beginner: "Beginner vocab", intermediate: "Intermediate vocab", advanced: "Advanced vocab" };
const ANALOGY_LABEL = { low: "Few analogies", medium: "Some analogies", high: "Analogy-heavy" };
const EXAMPLE_LABEL = { low: "Few examples", medium: "Some examples", high: "Example-rich" };

function ProfileRow({ profile, onTogglePin, onRename, onDelete }) {
  return (
    <div className="prow" style={{ alignItems: "flex-start" }}>
      <span
        className={`pin-cell ${profile.is_favorite ? "pin-on" : ""}`}
        onClick={() => onTogglePin(profile)}
        title={profile.is_favorite ? "Unpin" : "Pin"}
        style={{ marginTop: 3 }}
      >
        <Icon name="pin" size={16} />
      </span>
      <div className="avatar">{profile.display_name.slice(0, 2).toUpperCase()}</div>
      <div className="prow-id" style={{ flex: 1 }}>
        <div className="prow-name">{profile.display_name}</div>
        <div className="prow-tags" style={{ marginTop: 6 }}>
          {profile.pacing && (
            <Badge variant="primary">{PACING_LABEL[profile.pacing.toLowerCase()] || profile.pacing}</Badge>
          )}
          {profile.vocabulary_level && (
            <Badge variant="iris">{VOCAB_LABEL[profile.vocabulary_level.toLowerCase()] || profile.vocabulary_level}</Badge>
          )}
          {profile.analogy_frequency && (
            <Badge variant="amber">{ANALOGY_LABEL[profile.analogy_frequency.toLowerCase()] || profile.analogy_frequency}</Badge>
          )}
          {profile.example_density && (
            <Badge variant="plum">{EXAMPLE_LABEL[profile.example_density.toLowerCase()] || profile.example_density}</Badge>
          )}
        </div>
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

function TabBar({ tab, setTab }) {
  return (
    <div className="tab-bar">
      <button className={`tab-btn ${tab === "teaching" ? "tab-btn-on" : ""}`} onClick={() => setTab("teaching")}>Teaching styles</button>
      <button className={`tab-btn ${tab === "coding" ? "tab-btn-on" : ""}`} onClick={() => setTab("coding")}>Coding styles</button>
    </div>
  );
}

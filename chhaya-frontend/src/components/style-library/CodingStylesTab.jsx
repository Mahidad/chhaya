import { useEffect, useState } from "react";
import Button from "../ui/Button";
import Badge from "../ui/Badge";
import Icon from "../icons/Icon";
import { TextField, SelectField } from "../ui/Field";
import {
  listCodeStyleProfiles,
  createCodeStyleProfile,
  updateCodeStyleProfile,
  deleteCodeStyleProfile,
} from "../../api/codeStyleProfiles";

/*
  The other half of the unified Style Library -- coding style profiles,
  extracted by the crude regex-based analyzer (app/utils/code_style_analyzer.py
  on the backend, zero AI involved), used by the HLL Code Converter to
  write translated/generated code the way the student already writes it.

  Structurally a sibling to the Teaching styles tab (same pin/rename/
  delete pattern) but genuinely different data underneath -- indentation,
  naming convention, loop/branching habits, complexity, not
  pacing/vocabulary/analogies.
*/

const LANGUAGES = ["python", "java", "cpp", "javascript", "c"];
const LANGUAGE_LABELS = { python: "Python", java: "Java", cpp: "C++", javascript: "JavaScript", c: "C" };

const LOOP_LABELS = {
  for_dominant: "mostly for-loops",
  while_dominant: "mostly while-loops",
  comprehension_heavy: "comprehension-heavy",
  mixed: "mixed loop use",
  none: "no loops in sample",
};
const BRANCH_LABELS = {
  ternary_heavy: "ternary-heavy",
  switch_based: "switch-based",
  if_else_standard: "standard if/else",
  none: "no branching in sample",
};

export default function CodingStylesTab() {
  const [profiles, setProfiles] = useState(null);
  const [adding, setAdding] = useState(false);
  const [renaming, setRenaming] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const refresh = () => listCodeStyleProfiles().then(setProfiles);

  useEffect(() => {
    refresh();
  }, []);

  async function togglePin(profile) {
    setProfiles((prev) =>
      prev.map((p) => (p.id === profile.id ? { ...p, is_favorite: !p.is_favorite } : p))
    );
    await updateCodeStyleProfile(profile.id, { is_favorite: !profile.is_favorite });
  }

  async function confirmDelete() {
    await deleteCodeStyleProfile(deleting.id);
    setDeleting(null);
    refresh();
  }

  if (profiles === null) {
    return <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>;
  }

  return (
    <>
      <div className="page-actions" style={{ marginBottom: 16, justifyContent: "flex-end", display: "flex" }}>
        <Button icon={<Icon name="plus" size={16} />} onClick={() => setAdding(true)}>
          Add coding style
        </Button>
      </div>

      {profiles.length === 0 ? (
        <div className="list-card">
          <div className="lib-empty">
            <div className="lib-empty-title">No coding styles yet</div>
            <div className="lib-empty-copy">
              Paste a sample of code from someone whose style you want to write in -- your own past work,
              a senior's code, anything. Chhaya reads the indentation, naming, and structure, no AI involved.
            </div>
            <Button icon={<Icon name="plus" size={16} />} onClick={() => setAdding(true)}>
              Add your first coding style
            </Button>
          </div>
        </div>
      ) : (
        <div className="list-card">
          {profiles.map((p) => (
            <div className="prow" key={p.id} style={{ alignItems: "flex-start" }}>
              <span
                className={`pin-cell ${p.is_favorite ? "pin-on" : ""}`}
                onClick={() => togglePin(p)}
                title={p.is_favorite ? "Unpin" : "Pin"}
                style={{ marginTop: 3 }}
              >
                <Icon name="pin" size={16} />
              </span>
              <div className="avatar av-plum">{"<>"}</div>
              <div className="prow-id" style={{ flex: 1 }}>
                <div className="prow-name">{p.label}</div>
                <div className="prow-course">{LANGUAGE_LABELS[p.language] || p.language}</div>
                <div className="prow-tags" style={{ marginTop: 6 }}>
                  <Badge>{p.indent_size} {p.indent_style}</Badge>
                  <Badge>{p.naming_convention}</Badge>
                  {p.brace_style && <Badge>{p.brace_style.replace("_", " ")} braces</Badge>}
                  <Badge variant="iris">{LOOP_LABELS[p.loop_style]}</Badge>
                  <Badge variant="plum">{BRANCH_LABELS[p.branching_style]}</Badge>
                  <Badge variant={p.cyclomatic_complexity > 8 ? "amber" : undefined}>
                    complexity {p.cyclomatic_complexity}
                  </Badge>
                </div>
              </div>
              <div className="prow-act">
                <button className="mini-btn" onClick={() => setRenaming(p)} title="Rename">
                  <Icon name="fileText" size={15} />
                </button>
                <button className="mini-btn" onClick={() => setDeleting(p)} title="Delete">
                  <Icon name="trash" size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {adding && (
        <AddCodingStyleDialog
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            refresh();
          }}
        />
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
        <div className="overlay" onClick={() => setDeleting(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-danger"><Icon name="trash" size={20} /></div>
              <div className="dialog-title">Delete "{deleting.label}"?</div>
              <div className="dialog-copy">This can't be undone.</div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setDeleting(null)}>Keep it</Button>
              <Button variant="danger" onClick={confirmDelete}>Delete</Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function AddCodingStyleDialog({ onClose, onSaved }) {
  const [label, setLabel] = useState("");
  const [language, setLanguage] = useState("python");
  const [sampleCode, setSampleCode] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSave() {
    setError("");
    setSaving(true);
    try {
      await createCodeStyleProfile({ label, language, sampleCode });
      onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not analyze that sample.");
      setSaving(false);
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="dialog" style={{ width: 560 }} onClick={(e) => e.stopPropagation()}>
        <div className="dialog-pad">
          <div className="dialog-icon di-primary"><Icon name="code" size={20} /></div>
          <div className="dialog-title">Add a coding style</div>
          <div className="dialog-copy" style={{ marginBottom: 12 }}>
            Paste at least a few functions' worth of code for a reliable read -- a couple of lines won't
            give the analyzer enough to work with.
          </div>
          <div className="row-2" style={{ marginBottom: 10 }}>
            <TextField label="Label" placeholder="Senior dev's style" value={label} onChange={(e) => setLabel(e.target.value)} />
            <SelectField label="Language" value={language} onChange={(e) => setLanguage(e.target.value)}>
              {LANGUAGES.map((l) => <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>)}
            </SelectField>
          </div>
          <div className="field">
            <div className="label">Sample code</div>
            <textarea
              className="conv-textarea"
              style={{ minHeight: 180, border: "1px solid var(--line)", borderRadius: 8 }}
              value={sampleCode}
              onChange={(e) => setSampleCode(e.target.value)}
              spellCheck={false}
            />
          </div>
          {error && <div className="error-text" style={{ marginTop: 8 }}>{error}</div>}
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving || !label.trim() || !sampleCode.trim()}>
            {saving ? "Analyzing..." : "Analyze and save"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function RenameDialog({ profile, onClose, onSaved }) {
  const [label, setLabel] = useState(profile.label);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await updateCodeStyleProfile(profile.id, { label });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-pad">
          <div className="dialog-icon di-primary"><Icon name="fileText" size={20} /></div>
          <div className="dialog-title">Rename style</div>
          <div className="field" style={{ marginTop: 14 }}>
            <div className="input">
              <input
                autoFocus
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                style={{ border: "none", outline: "none", background: "transparent", flex: 1 }}
              />
            </div>
          </div>
        </div>
        <div className="dialog-foot">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving || !label.trim()}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}

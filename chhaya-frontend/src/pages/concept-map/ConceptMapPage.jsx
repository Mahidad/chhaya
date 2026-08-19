import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { TextField, SelectField } from "../../components/ui/Field";
import ConceptMapGame from "../../components/concept-map/ConceptMapGame";
import {
  listConceptMaps,
  createConceptMap,
  deleteConceptMap,
} from "../../api/conceptMaps";

/*
  Module 3 Feature 2 (Lamia) -- concept map recall game.

  Two views in one page: a list of saved maps + a create form, and the
  game board itself once a map is opened. Kept in one file because the
  list view is small and always leads directly into the game.
*/

const SOURCE_KINDS = [
  { value: "text", label: "Text / notes", hint: "Prose about any topic — nodes come from noun phrases." },
  { value: "math", label: "Formula", hint: "e.g. E = m * c^2 — variables become puzzle pieces." },
  { value: "code", label: "Python code", hint: "Classes, functions, and what calls what." },
];

export default function ConceptMapPage() {
  const [maps, setMaps] = useState(null);
  const [activeMap, setActiveMap] = useState(null);
  const [creating, setCreating] = useState(false);

  const [title, setTitle] = useState("");
  const [sourceKind, setSourceKind] = useState("text");
  const [sourceText, setSourceText] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const refresh = () => listConceptMaps().then(setMaps).catch(() => setMaps([]));

  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate() {
    setError("");
    setSaving(true);
    try {
      const created = await createConceptMap({ title, sourceText, sourceKind });
      setCreating(false);
      setTitle("");
      setSourceText("");
      refresh();
      setActiveMap(created); // jump straight into the game
    } catch (err) {
      setError(err.response?.data?.detail || "Could not build a map from that.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(map, e) {
    e.stopPropagation();
    await deleteConceptMap(map.id);
    refresh();
  }

  if (activeMap) {
    return (
      <AppShell section="Concept maps" current={activeMap.title}>
        <div className="page-head">
          <div>
            <div className="page-title">{activeMap.title}</div>
            <div className="page-sub">Drag each concept onto the slot where it belongs.</div>
          </div>
        </div>
        <ConceptMapGame conceptMap={activeMap} onExit={() => setActiveMap(null)} />
      </AppShell>
    );
  }

  return (
    <AppShell section="Concept maps" current="All maps">
      <div className="page-head">
        <div>
          <div className="page-title">Concept maps</div>
          <div className="page-sub">
            Turn notes, formulas, or code into a recall game — rebuild the map from memory.
          </div>
        </div>
        <div className="page-actions">
          <Button icon={<Icon name="plus" size={16} />} onClick={() => setCreating(true)}>
            New concept map
          </Button>
        </div>
      </div>

      {maps === null ? (
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      ) : maps.length === 0 ? (
        <div className="list-card">
          <div className="lib-empty">
            <div className="lib-empty-title">No concept maps yet</div>
            <div className="lib-empty-copy">
              Paste a passage from your notes, a formula, or some Python — Chhaya pulls out the key
              concepts and shuffles them into a puzzle for you to rebuild.
            </div>
            <Button icon={<Icon name="plus" size={16} />} onClick={() => setCreating(true)}>
              Build your first map
            </Button>
          </div>
        </div>
      ) : (
        <div className="list-card">
          {maps.map((m) => (
            <div className="saved-item-row" key={m.id} onClick={() => setActiveMap(m)}>
              <Icon name="conceptMap" size={14} />
              <span className="saved-item-title">{m.title}</span>
              <Badge>{m.source_kind}</Badge>
              <span className="saved-item-meta">{m.nodes.length} concepts</span>
              <button className="mini-btn" onClick={(e) => handleDelete(m, e)} title="Delete">
                <Icon name="trash" size={13} />
              </button>
            </div>
          ))}
        </div>
      )}

      {creating && (
        <div className="overlay" onClick={() => setCreating(false)}>
          <div className="dialog" style={{ width: 560 }} onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-primary">
                <Icon name="conceptMap" size={20} />
              </div>
              <div className="dialog-title">New concept map</div>

              <div className="row-2" style={{ marginTop: 14, marginBottom: 10 }}>
                <TextField
                  label="Title"
                  placeholder="Black holes"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
                <SelectField
                  label="Source type"
                  value={sourceKind}
                  onChange={(e) => setSourceKind(e.target.value)}
                >
                  {SOURCE_KINDS.map((k) => (
                    <option key={k.value} value={k.value}>{k.label}</option>
                  ))}
                </SelectField>
              </div>
              <div className="hint" style={{ marginBottom: 10 }}>
                {SOURCE_KINDS.find((k) => k.value === sourceKind)?.hint}
              </div>

              <div className="field">
                <div className="label">Source</div>
                <textarea
                  className="conv-textarea"
                  style={{ minHeight: 160, border: "1px solid var(--line)", borderRadius: 8 }}
                  value={sourceText}
                  onChange={(e) => setSourceText(e.target.value)}
                  spellCheck={false}
                />
              </div>
              {error && <div className="error-text" style={{ marginTop: 8 }}>{error}</div>}
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setCreating(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={saving || !title.trim() || !sourceText.trim()}>
                {saving ? "Building..." : "Build map"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

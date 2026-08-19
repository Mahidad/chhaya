import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import Badge from "../../components/ui/Badge";
import { listConceptMaps, deleteConceptMap } from "../../api/conceptMaps";

/*
  Module 3 (Lamia) -- Concept Map active-recall game, list page. Same
  worked pattern as StudyGuidesListPage.jsx: fetch on mount, render
  list-or-empty, delete with a confirm dialog.
*/
export default function ConceptMapsListPage() {
  const navigate = useNavigate();
  const [maps, setMaps] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const refresh = () => listConceptMaps().then(setMaps);

  useEffect(() => {
    refresh();
  }, []);

  async function handleDelete() {
    if (!deleting) return;
    await deleteConceptMap(deleting.id);
    setDeleting(null);
    refresh();
  }

  if (maps === null) {
    return (
      <AppShell section="Concept maps" current="All games">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Concept maps" current="All games">
      <div className="page-head">
        <div>
          <div className="page-title">Concept maps</div>
          <div className="page-sub">
            {maps.length === 0
              ? "Turn a study guide or pasted notes into a quick fill-in-the-blank recall game."
              : `${maps.length} game${maps.length === 1 ? "" : "s"}.`}
          </div>
        </div>
        <div className="page-actions">
          <Button icon={<Icon name="plus" size={16} />} onClick={() => navigate("/concept-maps/new")}>
            New concept map
          </Button>
        </div>
      </div>

      {maps.length === 0 ? (
        <div className="list-card">
          <div className="lib-empty">
            <div className="lib-empty-title">No concept maps yet</div>
            <div className="lib-empty-copy">
              Paste some notes or pick a study guide, and Chhaya will pull out key terms and formulas
              and turn them into a quick drag-and-drop recall game -- no AI needed to check your answers.
            </div>
            <Button icon={<Icon name="plus" size={16} />} onClick={() => navigate("/concept-maps/new")}>
              Make your first concept map
            </Button>
          </div>
        </div>
      ) : (
        <div className="list-card">
          {maps.map((m) => (
            <div key={m.id} className="prow">
              <Icon name="conceptMap" size={16} />
              <div
                className="prow-id"
                style={{ flex: 1, cursor: m.status === "ready" ? "pointer" : "default" }}
                onClick={() => m.status === "ready" && navigate(`/concept-maps/${m.id}/play`)}
              >
                <div className="prow-name">{m.title}</div>
              </div>
              <Badge variant="iris">{m.extraction_mode === "formula" ? "Formulas" : "Text"}</Badge>
              {m.is_basic_mode && <Badge variant="amber">Basic extraction</Badge>}
              <Badge variant={m.status === "ready" ? "ok" : "danger"}>{m.status}</Badge>
              <div className="prow-act">
                <button className="mini-btn" onClick={() => setDeleting(m)} title="Delete">
                  <Icon name="trash" size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {deleting && (
        <div className="overlay" onClick={() => setDeleting(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-danger"><Icon name="trash" size={20} /></div>
              <div className="dialog-title">Delete "{deleting.title}"?</div>
              <div className="dialog-copy">Past attempts on this game are deleted too. This can't be undone.</div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setDeleting(null)}>Keep it</Button>
              <Button variant="danger" onClick={handleDelete}>Delete</Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

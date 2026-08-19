import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { listStudyGuides } from "../../api/studyGuides";
import { createConceptMap } from "../../api/conceptMaps";

/*
  Module 3 (Lamia) -- Concept Map generation form. No polling screen
  needed here (unlike ConfigureGuidePage.jsx) -- extraction is local
  NLTK/regex work, not an external AI call, so POST /concept-maps
  returns the finished game already 'ready' in one request/response.
*/
export default function GenerateConceptMapPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [extractionMode, setExtractionMode] = useState("text");
  const [sourceKind, setSourceKind] = useState("paste"); // "paste" | "guide"
  const [rawText, setRawText] = useState("");
  const [guides, setGuides] = useState(null);
  const [guideId, setGuideId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listStudyGuides().then((data) => {
      const ready = data.filter((g) => g.status === "ready");
      setGuides(ready);
      if (ready.length > 0) setGuideId(ready[0].id);
    });
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!title.trim()) { setError("Give this game a title."); return; }
    if (sourceKind === "paste" && !rawText.trim()) { setError("Paste in some text to build the game from."); return; }
    if (sourceKind === "guide" && !guideId) { setError("Pick a study guide."); return; }

    setSubmitting(true);
    setError("");
    try {
      const map = await createConceptMap({
        title: title.trim(),
        extractionMode,
        sourceStudyGuideId: sourceKind === "guide" ? guideId : null,
        rawText: sourceKind === "paste" ? rawText : null,
      });
      if (map.status === "failed") {
        setError(map.error_message || "Couldn't build a game from that text.");
        setSubmitting(false);
        return;
      }
      navigate(`/concept-maps/${map.id}/play`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create that concept map.");
      setSubmitting(false);
    }
  }

  return (
    <AppShell section="Concept maps" current="New concept map">
      <div className="page-head">
        <div>
          <div className="page-title">New concept map</div>
          <div className="page-sub">Pull key terms or formulas out of some text and turn them into a recall game.</div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card card-pad" style={{ maxWidth: 640, display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <div className="label" style={{ marginBottom: 6 }}>Title</div>
          <div className="input">
            <input
              placeholder="e.g. Thermodynamics formulas"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{ border: "none", outline: "none", background: "transparent", flex: 1 }}
            />
          </div>
        </div>

        <div>
          <div className="label" style={{ marginBottom: 6 }}>What kind of content is this?</div>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" className={`chip ${extractionMode === "text" ? "chip-on" : ""}`} onClick={() => setExtractionMode("text")}>
              General text (biology, definitions, ...)
            </button>
            <button type="button" className={`chip ${extractionMode === "formula" ? "chip-on" : ""}`} onClick={() => setExtractionMode("formula")}>
              Math formulas
            </button>
          </div>
          <div className="hint" style={{ marginTop: 4 }}>
            {extractionMode === "text"
              ? "Key terms are pulled out and blanked in the sentence they appear in."
              : "Each equation's left-hand symbol (e.g. \"ΔU\" in \"ΔU = Q − W\") becomes a blank."}
          </div>
        </div>

        <div>
          <div className="label" style={{ marginBottom: 6 }}>Source</div>
          <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
            <button type="button" className={`chip ${sourceKind === "paste" ? "chip-on" : ""}`} onClick={() => setSourceKind("paste")}>
              Paste text
            </button>
            <button type="button" className={`chip ${sourceKind === "guide" ? "chip-on" : ""}`} onClick={() => setSourceKind("guide")}>
              From a study guide
            </button>
          </div>

          {sourceKind === "paste" ? (
            <textarea
              className="annot-sticky-textarea"
              style={{ minHeight: 160, width: "100%" }}
              placeholder="Paste a few paragraphs, or a list of formulas..."
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
            />
          ) : guides === null ? (
            <div className="hint">Loading your study guides...</div>
          ) : guides.length === 0 ? (
            <div className="hint">No finished study guides yet -- generate one first, or paste text instead.</div>
          ) : (
            <select className="select" value={guideId} onChange={(e) => setGuideId(e.target.value)}>
              {guides.map((g) => <option key={g.id} value={g.id}>{g.topic}</option>)}
            </select>
          )}
        </div>

        {error && <div className="error-text">{error}</div>}

        <div>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Building game..." : "Generate concept map"}
          </Button>
        </div>
      </form>
    </AppShell>
  );
}

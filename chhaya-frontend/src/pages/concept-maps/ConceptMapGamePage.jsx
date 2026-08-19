import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { getConceptMap, recordAttempt } from "../../api/conceptMaps";

/*
  Module 3 (Lamia) -- Concept Map active-recall game. Deliberately no
  external drag-and-drop library and no canvas -- native HTML5 drag
  events cover desktop, and a click-to-place fallback (select a card,
  then tap a blank) covers touch/mobile, since HTML5 DnD doesn't fire on
  touch devices at all. Validation is exactly what the original brief
  asked for: one line, `draggedId === slot.answerItemId`, no AI call.
*/

function shuffle(arr) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export default function ConceptMapGamePage() {
  const { id } = useParams();
  const [map, setMap] = useState(null);
  const [filled, setFilled] = useState({});     // itemId -> true once correctly placed
  const [wrongFlash, setWrongFlash] = useState(null); // itemId currently showing a "try again" flash
  const [deckOrder, setDeckOrder] = useState([]); // shuffled item ids still in the deck
  const [selectedCardId, setSelectedCardId] = useState(null); // click-to-place fallback
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    getConceptMap(id).then((data) => {
      setMap(data);
      setDeckOrder(shuffle(data.items.map((it) => it.id)));
      setFilled({});
      setSubmitted(false);
    });
  }, [id]);

  const items = map?.items || [];
  const total = items.length;
  const correctCount = Object.keys(filled).length;
  const isComplete = total > 0 && correctCount === total;

  useEffect(() => {
    if (isComplete && !submitted) {
      recordAttempt(id, { correctCount, totalCount: total }).catch(() => {});
      setSubmitted(true);
    }
  }, [isComplete, submitted, id, correctCount, total]);

  function attemptPlace(itemId, droppedId) {
    if (filled[itemId]) return; // already solved, ignore
    if (droppedId === itemId) {
      setFilled((prev) => ({ ...prev, [itemId]: true }));
      setDeckOrder((prev) => prev.filter((x) => x !== droppedId));
    } else {
      setWrongFlash(itemId);
      setTimeout(() => setWrongFlash(null), 500);
    }
    setSelectedCardId(null);
  }

  function handlePlayAgain() {
    setDeckOrder(shuffle(items.map((it) => it.id)));
    setFilled({});
    setSubmitted(false);
    setSelectedCardId(null);
  }

  const answerById = useMemo(
    () => Object.fromEntries(items.map((it) => [it.id, it.answer])),
    [items]
  );

  if (map === null) {
    return (
      <AppShell section="Concept maps" current="Loading...">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Concept maps" current={map.title}>
      <div className="page-head">
        <div>
          <Link to="/concept-maps" className="hint" style={{ marginBottom: 4, display: "inline-block" }}>&larr; All concept maps</Link>
          <div className="page-title">{map.title}</div>
          <div className="page-sub">
            {correctCount} / {total} filled in
            {map.is_basic_mode && " · basic extraction (NLTK data not installed on the server)"}
          </div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" icon={<Icon name="fileText" size={16} />} onClick={handlePlayAgain}>
            Play again
          </Button>
        </div>
      </div>

      {isComplete && (
        <div className="card card-pad" style={{ marginBottom: 16, background: "var(--ok-soft)", borderColor: "var(--ok)" }}>
          <strong>Nice work!</strong> You filled in every blank correctly.
        </div>
      )}

      <div className="workspace-grid">
        <div className="workspace-main" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {items.map((item) => {
            const [before, after] = item.template.split("___");
            const isFilled = !!filled[item.id];
            const isWrongFlash = wrongFlash === item.id;

            return (
              <div key={item.id} className="card card-pad concept-sentence">
                {before}
                <span
                  className={`concept-blank ${isFilled ? "concept-blank-filled" : ""} ${isWrongFlash ? "concept-blank-wrong" : ""}`}
                  onDragOver={(e) => !isFilled && e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    attemptPlace(item.id, e.dataTransfer.getData("text/plain"));
                  }}
                  onClick={() => selectedCardId && attemptPlace(item.id, selectedCardId)}
                >
                  {isFilled ? answerById[item.id] : "\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0"}
                </span>
                {after}
              </div>
            );
          })}
        </div>

        <div className="workspace-side">
          <div className="card">
            <div className="card-head"><span className="card-title">Word bank</span></div>
            <div className="card-pad" style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {deckOrder.length === 0 ? (
                <div className="hint">All placed -- nice work!</div>
              ) : (
                deckOrder.map((itemId) => (
                  <div
                    key={itemId}
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData("text/plain", itemId)}
                    onClick={() => setSelectedCardId((cur) => (cur === itemId ? null : itemId))}
                    className={`chip concept-card ${selectedCardId === itemId ? "chip-on" : ""}`}
                  >
                    {answerById[itemId]}
                  </div>
                ))
              )}
            </div>
            <div className="card-pad hint" style={{ paddingTop: 0 }}>
              Drag a card onto a blank, or tap a card then tap the blank.
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

import { useMemo, useState } from "react";
import Button from "../ui/Button";
import Icon from "../icons/Icon";

/*
  Module 3 Feature 2 (Lamia) -- the concept-map recall game board.

  HOW THE GAME WORKS:
    - The map's nodes are laid out in a ring, but each one renders as an
      EMPTY slot showing only its connections.
    - The same node labels are shuffled into a deck on the right.
    - The student drags a label from the deck onto the slot they think it
      belongs to.
    - Validation compares each slot's `nodeId` against the id of whatever
      card was dropped on it. A win is every slot holding its own card.

  Kept deliberately simple per the spec: HTML5 drag-and-drop (which
  browsers give us for free) rather than a canvas + custom pointer
  physics, and an SVG ring layout rather than a force-directed graph
  library. Fewer moving parts to debug, and the learning value is in
  recalling which concept connects to which -- not in the visuals.

  Touch note: HTML5 drag events don't fire on most touch devices, so a
  tap-to-select / tap-to-place fallback runs alongside the drag handlers
  (see handleCardTap / handleSlotTap). Both paths end in the same
  placeCard(), so there's one code path for the actual game logic.
*/

const RADIUS = 150;
const CENTER = { x: 200, y: 175 };

function shuffle(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export default function ConceptMapGame({ conceptMap, onExit }) {
  const { nodes, edges } = conceptMap;

  // Fixed ring positions -- computed once per map so slots don't jump
  // around as the student plays.
  const positions = useMemo(() => {
    const map = {};
    nodes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      map[n.id] = {
        x: CENTER.x + RADIUS * Math.cos(angle),
        y: CENTER.y + RADIUS * Math.sin(angle),
      };
    });
    return map;
  }, [nodes]);

  const [deck, setDeck] = useState(() => shuffle(nodes));
  const [placements, setPlacements] = useState({}); // { slotNodeId: placedNode }
  const [selectedCard, setSelectedCard] = useState(null);
  const [checked, setChecked] = useState(false);

  const allPlaced = Object.keys(placements).length === nodes.length;
  const correctCount = Object.entries(placements).filter(([slotId, card]) => slotId === card.id).length;
  const hasWon = checked && correctCount === nodes.length;

  function placeCard(slotNodeId, card) {
    setChecked(false);
    setPlacements((prev) => {
      const next = { ...prev };
      // If this card was already on another slot, take it off that one.
      for (const [sid, c] of Object.entries(next)) {
        if (c.id === card.id) delete next[sid];
      }
      // If the target slot already had a card, send that one back to the deck.
      const displaced = next[slotNodeId];
      next[slotNodeId] = card;
      if (displaced && displaced.id !== card.id) {
        setDeck((d) => [...d, displaced]);
      }
      return next;
    });
    setDeck((d) => d.filter((c) => c.id !== card.id));
    setSelectedCard(null);
  }

  function returnToDeck(slotNodeId) {
    setChecked(false);
    setPlacements((prev) => {
      const next = { ...prev };
      const card = next[slotNodeId];
      delete next[slotNodeId];
      if (card) setDeck((d) => (d.some((c) => c.id === card.id) ? d : [...d, card]));
      return next;
    });
  }

  function handleReset() {
    setDeck(shuffle(nodes));
    setPlacements({});
    setSelectedCard(null);
    setChecked(false);
  }

  function handleCardTap(card) {
    setSelectedCard((cur) => (cur?.id === card.id ? null : card));
  }

  function handleSlotTap(slotNodeId) {
    if (selectedCard) placeCard(slotNodeId, selectedCard);
    else if (placements[slotNodeId]) returnToDeck(slotNodeId);
  }

  return (
    <div className="game-layout">
      <div className="game-board card">
        <div className="card-head">
          <span className="card-title">{conceptMap.title}</span>
          <span className="card-note">
            {Object.keys(placements).length} / {nodes.length} placed
          </span>
        </div>

        <svg viewBox="0 0 400 350" className="game-svg">
          {edges.map((e, i) => {
            const a = positions[e.source];
            const b = positions[e.target];
            if (!a || !b) return null;
            return (
              <g key={i}>
                <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} className="game-edge" />
                <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 4} className="game-edge-label">
                  {e.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Slots are positioned HTML (not SVG) so they can accept real
            drag-and-drop events, which SVG elements handle inconsistently. */}
        <div className="game-slots">
          {nodes.map((n) => {
            const placed = placements[n.id];
            const isCorrect = checked && placed && placed.id === n.id;
            const isWrong = checked && placed && placed.id !== n.id;
            return (
              <div
                key={n.id}
                className={`game-slot ${placed ? "game-slot-filled" : ""} ${isCorrect ? "game-slot-correct" : ""} ${isWrong ? "game-slot-wrong" : ""}`}
                style={{ left: positions[n.id].x, top: positions[n.id].y }}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const card = JSON.parse(e.dataTransfer.getData("application/json"));
                  placeCard(n.id, card);
                }}
                onClick={() => handleSlotTap(n.id)}
              >
                {placed ? placed.label : "?"}
              </div>
            );
          })}
        </div>

        <div className="game-actions">
          <Button size="sm" onClick={() => setChecked(true)} disabled={!allPlaced}>
            Check answers
          </Button>
          <Button size="sm" variant="ghost" icon={<Icon name="refresh" size={14} />} onClick={handleReset}>
            Reset
          </Button>
          {onExit && (
            <Button size="sm" variant="ghost" onClick={onExit} style={{ marginLeft: "auto" }}>
              Back
            </Button>
          )}
        </div>

        {checked && (
          <div className={`game-result ${hasWon ? "game-result-win" : "game-result-partial"}`}>
            {hasWon
              ? "Every concept is in the right place."
              : `${correctCount} of ${nodes.length} correct — the highlighted ones need another look.`}
          </div>
        )}
      </div>

      <div className="game-deck card">
        <div className="card-head">
          <span className="card-title">Deck</span>
          <span className="card-note">{deck.length} left</span>
        </div>
        <div className="deck-cards">
          {deck.length === 0 ? (
            <div className="hint">All placed — press Check answers.</div>
          ) : (
            deck.map((card) => (
              <div
                key={card.id}
                className={`deck-card ${selectedCard?.id === card.id ? "deck-card-selected" : ""}`}
                draggable
                onDragStart={(e) => e.dataTransfer.setData("application/json", JSON.stringify(card))}
                onClick={() => handleCardTap(card)}
              >
                {card.label}
              </div>
            ))
          )}
        </div>
        {selectedCard && (
          <div className="hint" style={{ padding: "0 12px 12px" }}>
            Now tap an empty slot to place "{selectedCard.label}".
          </div>
        )}
      </div>
    </div>
  );
}

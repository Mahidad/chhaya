import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import Icon from "../icons/Icon";
import Button from "../ui/Button";
import { listHighlights, createHighlight, deleteHighlight } from "../../api/annotations";
import { lookupWord, saveGlossaryEntry } from "../../api/glossary";

export const AnnotationContext = createContext(null);

function getSelectionOffset(container) {
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount) return 0;
  const range = sel.getRangeAt(0);
  const preSelectionRange = range.cloneRange();
  preSelectionRange.selectNodeContents(container);
  preSelectionRange.setEnd(range.startContainer, range.startOffset);
  return preSelectionRange.toString().length;
}

// A chapter that hasn't actually been chosen yet (see GuideDetailPage's
// effectiveChapterId fallback) is represented as the literal string
// "unfiled" so every child component has one consistent way to ask "is
// this content actually filed anywhere?" without checking for null,
// undefined, and "unfiled" separately in three different places.
function isRealChapter(chapterId) {
  return !!chapterId && chapterId !== "unfiled";
}

export function HighlightableText({ children }) {
  const context = useContext(AnnotationContext);
  if (!context) return children;

  let childrenStr = "";
  if (typeof children === "string") {
    childrenStr = children;
  } else if (Array.isArray(children)) {
    childrenStr = children.map(c => (typeof c === "string" ? c : "")).join("");
  } else {
    return children;
  }

  if (!childrenStr) return children;

  const { highlights, charCounter, placedHighlights } = context;

  const startOffset = charCounter.current;
  charCounter.current += childrenStr.length;

  const markers = [];

  highlights.forEach((h) => {
    if (!h.quoted_text || placedHighlights.current.has(h.id)) return;

    let text = h.quoted_text;
    let hintOffset = -1;
    if (h.quoted_text.includes("|")) {
      const idx = h.quoted_text.indexOf("|");
      hintOffset = parseInt(h.quoted_text.slice(0, idx), 10);
      text = h.quoted_text.slice(idx + 1);
    }

    // PRIMARY: the recorded offset falls inside this fragment's range,
    // and the text actually sitting there still matches exactly. This is
    // the fast, exact path -- correct as long as nothing has been edited
    // since the highlight was created.
    if (hintOffset >= startOffset && hintOffset < startOffset + childrenStr.length) {
      const localPos = hintOffset - startOffset;
      if (childrenStr.slice(localPos, localPos + text.length) === text) {
        markers.push({ localOffset: localPos, text, data: h });
        placedHighlights.current.add(h.id);
        return;
      }
    }

    // FALLBACK: the text has moved (content was edited elsewhere) --
    // find it by its actual content instead of trusting the stale
    // offset. `placedHighlights` guarantees this only ever happens once
    // per highlight per render, even if the same phrase appears more
    // than once in the document, so a highlight can never "jump" onto
    // every matching word -- only the first fragment (in document order)
    // that still contains the exact text claims it.
    const pos = childrenStr.indexOf(text);
    if (pos !== -1) {
      markers.push({ localOffset: pos, text, data: h });
      placedHighlights.current.add(h.id);
    }
  });

  if (markers.length === 0) return children;
  markers.sort((a, b) => a.localOffset - b.localOffset);

  const result = [];
  let lastIndex = 0;

  for (const marker of markers) {
    if (marker.localOffset < lastIndex) continue;

    if (marker.localOffset > lastIndex) {
      result.push(childrenStr.slice(lastIndex, marker.localOffset));
    }

    const matchText = childrenStr.slice(marker.localOffset, marker.localOffset + marker.text.length);

    result.push(
      <mark
        key={marker.data.id}
        data-highlight-id={marker.data.id}
        style={{ backgroundColor: "#ffcc80", borderRadius: "2px", padding: "0 2px" }}
      >
        {matchText}
      </mark>
    );

    lastIndex = marker.localOffset + marker.text.length;
  }

  if (lastIndex < childrenStr.length) {
    result.push(childrenStr.slice(lastIndex));
  }

  return <>{result}</>;
}

export default function AnnotatableText({ chapterId, contentType, contentId, topic, readOnly = false, children }) {
  const [highlights, setHighlights] = useState([]);
  const [selection, setSelection] = useState(null); // { text, x, y, highlightId } | null
  const [lookup, setLookup] = useState(null); // { word, definition, ... } | null
  const containerRef = useRef(null);
  const charCounter = useRef(0);
  // Reset once per render pass (see charCounter.current = 0 below) and
  // filled in as HighlightableText places each highlight -- prevents the
  // same highlight id from being drawn twice if its exact text happens to
  // appear more than once in the document (this is what fixed "every
  // occurrence of a repeated word shows as highlighted").
  const placedHighlights = useRef(new Set());

  const refresh = () => {
    if (readOnly) return;
    listHighlights(contentType, contentId).then(setHighlights);
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentType, contentId, readOnly]);

  // Reset both counters before every render of children.
  charCounter.current = 0;
  placedHighlights.current = new Set();

  function handleMouseUp() {
    const sel = window.getSelection();
    const text = sel ? sel.toString().trim() : "";
    if (!text || !containerRef.current) {
      setSelection(null);
      return;
    }
    if (!containerRef.current.contains(sel.anchorNode)) {
      setSelection(null);
      return;
    }
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // If the click/selection is actually sitting inside an existing
    // highlight <mark>, read its real id straight off the DOM rather
    // than guessing by matching text against every highlight in the
    // document. This is what fixes "Undo highlight" showing up for a
    // plain, unhighlighted occurrence of a word just because some other
    // occurrence of the same word is highlighted elsewhere.
    let anchorEl = sel.anchorNode;
    if (anchorEl && anchorEl.nodeType === Node.TEXT_NODE) anchorEl = anchorEl.parentElement;
    const markEl = anchorEl ? anchorEl.closest("mark[data-highlight-id]") : null;

    setSelection({
      text,
      x: rect.left + rect.width / 2,
      y: rect.top,
      highlightId: markEl ? markEl.dataset.highlightId : null,
    });
    setLookup(null);
  }

  async function handleHighlight() {
    if (!selection || readOnly) return;
    try {
      const offset = getSelectionOffset(containerRef.current);
      await createHighlight({
        chapterId, contentType, contentId, quotedText: `${offset}|${selection.text}`, color: "amber",
      });
    } catch (err) {
      console.error("Failed to save highlight:", err);
      alert("Failed to save highlight. Please try again.");
      return;
    }
    setSelection(null);
    window.getSelection()?.removeAllRanges();
    refresh();
  }

  // The current selection sits inside an existing highlight only if the
  // DOM told us so in handleMouseUp -- a real, specific highlight id,
  // never a fuzzy text match.
  const overlappingHighlight = selection?.highlightId
    ? highlights.find((h) => h.id === selection.highlightId)
    : null;

  async function handleUndoHighlight() {
    if (!overlappingHighlight) return;
    await deleteHighlight(overlappingHighlight.id);
    setSelection(null);
    window.getSelection()?.removeAllRanges();
    refresh();
  }

  async function handleDefine() {
    if (!selection) return;
    const firstWord = selection.text.trim().split(/\s+/)[0].replace(/[^a-zA-Z'-]/g, "");
    const result = await lookupWord(firstWord, topic);
    setLookup(result);
  }

  async function handleSaveToGlossary() {
    // A guide that isn't filed into a chapter yet has nowhere for a
    // glossary entry to live (glossary_entries is scoped to a chapter),
    // so this is a hard no-op rather than letting the request go out and
    // fail server-side.
    if (!lookup || readOnly || !isRealChapter(chapterId)) return;
    await saveGlossaryEntry({
      chapterId, term: lookup.word, definition: lookup.definition,
      partOfSpeech: lookup.part_of_speech, source: lookup._mock ? "custom" : "wordnet",
    });
    setLookup(null);
    setSelection(null);
    window.getSelection()?.removeAllRanges();
  }

  return (
    <AnnotationContext.Provider value={{ highlights, charCounter, placedHighlights }}>
      <div style={{ position: "relative" }}>
        <div ref={containerRef} onMouseUp={handleMouseUp}>
          {children}
        </div>

        {/* Floating selection toolbar */}
        {selection && !lookup && (
          <div
            className="annot-toolbar"
            style={{ position: "fixed", left: selection.x, top: selection.y - 44 }}
          >
            {!readOnly && (
              overlappingHighlight ? (
                <button className="annot-toolbar-btn" onClick={handleUndoHighlight} title="Undo highlight">
                  <Icon name="trash" size={14} /> Undo highlight
                </button>
              ) : (
                <button className="annot-toolbar-btn" onClick={handleHighlight} title="Highlight">
                  <Icon name="fileText" size={14} /> Highlight
                </button>
              )
            )}
            <button className="annot-toolbar-btn" onClick={handleDefine} title="Look up definition">
              <Icon name="search" size={14} /> Define
            </button>
          </div>
        )}

        {/* Definition popover */}
        {lookup && selection && (
          <div className="annot-toolbar annot-define-popover" style={{ position: "fixed", left: selection.x, top: selection.y - 20 }}>
            <div style={{ fontWeight: 700, fontSize: 13 }}>
              {lookup.word} {lookup.part_of_speech && <span className="hint">({lookup.part_of_speech})</span>}
            </div>
            <div style={{ fontSize: 12, color: "var(--ink-2)", margin: "4px 0 8px" }}>{lookup.definition}</div>
            {lookup.synonyms?.length > 0 && (
              <div className="hint" style={{ marginBottom: 8 }}>Similar: {lookup.synonyms.join(", ")}</div>
            )}
            <div style={{ display: "flex", gap: 6 }}>
              {!readOnly && (
                <Button
                  size="sm"
                  onClick={handleSaveToGlossary}
                  disabled={!isRealChapter(chapterId)}
                  title={!isRealChapter(chapterId) ? "File this guide into a chapter first to save glossary words" : undefined}
                >
                  Save to glossary
                </Button>
              )}
              <Button size="sm" variant="ghost" onClick={() => { setLookup(null); setSelection(null); }}>Close</Button>
            </div>
          </div>
        )}
      </div>
    </AnnotationContext.Provider>
  );
}

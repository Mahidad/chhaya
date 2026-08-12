import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import CodeLines from "../../components/code-converter/CodeLines";
import { listCodeStyleProfiles } from "../../api/codeStyleProfiles";
import { translateCode, solveProblem } from "../../api/codeConversions";

/*
  The HLL Code Converter. Two modes sharing one page:
    - "translate": paste code in one language, read it in another,
      side by side, with click-to-highlight between the two.
    - "solve": describe a problem, get a fresh solution in the chosen
      language (and optionally a chosen coding style) -- no source pane,
      since there's nothing to translate from.

  BOTH MODES CALL GEMINI (see app/services/code_conversion_service.py on
  the backend) -- this is the one feature in the app that genuinely can't
  be reproduced without AI, a deliberate trade-off made explicitly for
  translation quality and language breadth. The coding-style *extraction*
  used here (Style Library's "Coding styles" tab) stays AI-free.

  CLICK-TO-HIGHLIGHT: the backend returns `mapping`, a list of
  {source_lines: [start,end], output_lines: [start,end], description}
  blocks. Clicking a line finds the block whose range contains it and
  sets it as `activeMapping` -- both CodeLines components read their
  highlighted range off the same piece of state, so clicking either side
  highlights both.
*/

const LANGUAGES = ["python", "java", "cpp", "javascript", "c"];
const LANGUAGE_LABELS = { python: "Python", java: "Java", cpp: "C++", javascript: "JavaScript", c: "C" };

export default function CodeConverterPage() {
  const [mode, setMode] = useState("translate"); // "translate" | "solve"
  const [sourceLanguage, setSourceLanguage] = useState(""); // "" = auto-detect
  const [targetLanguage, setTargetLanguage] = useState("java");
  const [sourceCode, setSourceCode] = useState("");
  const [problemStatement, setProblemStatement] = useState("");
  const [codeStyleProfileId, setCodeStyleProfileId] = useState("");
  const [styleProfiles, setStyleProfiles] = useState([]);

  const [conversion, setConversion] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [activeMapping, setActiveMapping] = useState(null);
  const [editing, setEditing] = useState(true); // true while the source pane is still an editable textarea

  useEffect(() => {
    listCodeStyleProfiles().then(setStyleProfiles).catch(() => setStyleProfiles([]));
  }, []);

  function switchMode(next) {
    setMode(next);
    setConversion(null);
    setError("");
    setActiveMapping(null);
    setEditing(true);
  }

  async function handleSubmit() {
    setError("");
    setSubmitting(true);
    setActiveMapping(null);
    try {
      const result =
        mode === "translate"
          ? await translateCode({
              sourceCode,
              sourceLanguage: sourceLanguage || null,
              targetLanguage,
              codeStyleProfileId,
            })
          : await solveProblem({ problemStatement, targetLanguage, codeStyleProfileId });

      setConversion(result);
      setEditing(false);
      if (result.status === "failed") {
        setError(result.error_message || "Something went wrong.");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not complete that request.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleSourceLineClick(lineNum) {
    if (!conversion?.mapping) return;
    const block = conversion.mapping.find(
      (b) => lineNum >= b.source_lines[0] && lineNum <= b.source_lines[1]
    );
    setActiveMapping(block || null);
  }

  function handleOutputLineClick(lineNum) {
    if (!conversion?.mapping) return;
    const block = conversion.mapping.find(
      (b) => lineNum >= b.output_lines[0] && lineNum <= b.output_lines[1]
    );
    setActiveMapping(block || null);
  }

  const canSubmit =
    mode === "translate" ? sourceCode.trim().length > 0 : problemStatement.trim().length > 0;

  return (
    <AppShell section="Code converter" current={mode === "translate" ? "Translate" : "Solve a problem"}>
      <div className="page-head">
        <div>
          <div className="page-title">HLL Code Converter</div>
          <div className="page-sub">
            {mode === "translate"
              ? "Paste code in one language, read it in another. Click a line on either side to see what matches."
              : "Describe a problem, get a solution written the way you'd want to write it."}
          </div>
        </div>
      </div>

      <div className="conv-shell">
        <div className="conv-mode-bar">
          <button className={`mode-btn ${mode === "translate" ? "mode-btn-on" : ""}`} onClick={() => switchMode("translate")}>
            <Icon name="swap" size={15} /> Translate code
          </button>
          <button className={`mode-btn ${mode === "solve" ? "mode-btn-on" : ""}`} onClick={() => switchMode("solve")}>
            <Icon name="wand" size={15} /> Solve a problem
          </button>
        </div>

        <div className="conv-panes">
          {/* ---------- left pane: source code or problem statement ---------- */}
          <div className="conv-pane card">
            <div className="conv-pane-head">
              <span className="conv-pane-title">{mode === "translate" ? "Source" : "Problem"}</span>
              {mode === "translate" && (
                <select className="conv-select" value={sourceLanguage} onChange={(e) => setSourceLanguage(e.target.value)}>
                  <option value="">Auto-detect</option>
                  {LANGUAGES.map((l) => (
                    <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>
                  ))}
                </select>
              )}
              {mode === "translate" && conversion?.status === "ready" && conversion.source_language && (
                <span className="hint">detected: {LANGUAGE_LABELS[conversion.source_language] || conversion.source_language}</span>
              )}
              {mode === "translate" && !editing && (
                <button className="mini-btn" style={{ marginLeft: "auto" }} onClick={() => setEditing(true)} title="Edit source">
                  <Icon name="fileText" size={14} />
                </button>
              )}
            </div>

            {mode === "translate" ? (
              editing ? (
                <textarea
                  className="conv-textarea"
                  placeholder="Paste your source code here..."
                  value={sourceCode}
                  onChange={(e) => setSourceCode(e.target.value)}
                  spellCheck={false}
                />
              ) : (
                <CodeLines code={sourceCode} activeRange={activeMapping?.source_lines} onLineClick={handleSourceLineClick} />
              )
            ) : (
              <textarea
                className="conv-textarea"
                placeholder="Describe the problem you want solved, e.g. 'write a function that checks if a string is a palindrome'"
                value={problemStatement}
                onChange={(e) => setProblemStatement(e.target.value)}
              />
            )}
          </div>

          {/* ---------- right pane: output ---------- */}
          <div className="conv-pane card">
            <div className="conv-pane-head">
              <span className="conv-pane-title">Output</span>
              <select
                className="conv-select conv-select-right"
                value={codeStyleProfileId}
                onChange={(e) => setCodeStyleProfileId(e.target.value)}
                title="Coding style"
              >
                <option value="">Default style</option>
                {styleProfiles.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
              <select className="conv-select" value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
                {LANGUAGES.map((l) => (
                  <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>
                ))}
              </select>
            </div>

            {!conversion ? (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--faint)", fontSize: 13, minHeight: 320 }}>
                {mode === "translate" ? "Translated code will appear here" : "Your solution will appear here"}
              </div>
            ) : conversion.status === "generating" || conversion.status === "pending" ? (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", minHeight: 320 }}>
                <div className="progress" style={{ width: "60%" }}>
                  <div className="progress-fill" style={{ width: "45%", animation: "chhaya-indeterminate 1.4s ease-in-out infinite" }} />
                </div>
              </div>
            ) : conversion.status === "failed" ? (
              <div style={{ padding: 18 }}>
                <div className="banner banner-danger" style={{ marginBottom: 0 }}>
                  <Icon name="alertTriangle" size={18} />
                  <div>
                    <div className="banner-title">Could not generate output</div>
                    <div className="banner-copy">{conversion.error_message}</div>
                  </div>
                </div>
              </div>
            ) : (
              <CodeLines code={conversion.output_code} activeRange={activeMapping?.output_lines} onLineClick={handleOutputLineClick} />
            )}

            {activeMapping?.description && (
              <div className="conv-block-desc">{activeMapping.description}</div>
            )}
            {conversion?.status === "ready" && conversion.explanation && (
              <div className="conv-foot">
                <div className="hint">{conversion.explanation}</div>
              </div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Button
            icon={<Icon name={mode === "translate" ? "swap" : "wand"} size={16} />}
            onClick={handleSubmit}
            disabled={!canSubmit || submitting}
          >
            {submitting ? "Working..." : mode === "translate" ? "Translate" : "Solve"}
          </Button>
          {error && <div className="error-text">{error}</div>}
        </div>
      </div>
    </AppShell>
  );
}

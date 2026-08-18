import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import CodeLines from "../../components/code-studio/CodeLines";
import VariableWatchTable from "../../components/code-studio/VariableWatchTable";
import FolderSidebar from "../../components/code-studio/FolderSidebar";
import PracticePane from "../../components/code-studio/PracticePane";
import DashboardPane from "../../components/code-studio/DashboardPane";
import { listCodeStyleProfiles } from "../../api/codeStyleProfiles";
import { translateCode, solveProblem, listConversions, updateConversion, deleteConversion } from "../../api/codeConversions";
import { visualizeCode, listVisualizations, updateVisualization, deleteVisualization } from "../../api/codeVisualizations";
import {
  listCodeWorkspaceFolders,
  createCodeWorkspaceFolder,
  deleteCodeWorkspaceFolder,
} from "../../api/codeWorkspaceFolders";

/*
  Code Studio: three tools sharing one page and one storage system.
    - "translate": paste code, read it in another language, click-to-highlight.
    - "solve": describe a problem, get a fresh solution.
    - "visualize": paste code (or send it here from Translate/Solve's
      output via "Visualize this"), get a step-by-step variable-watch
      trace -- AI-simulated (see app/services/code_visualization_service.py
      for how the prompt is written to keep that trace as accurate as
      possible despite not being a real sandboxed execution).

  STORAGE: every translate/solve/visualize call already persists to the
  database the moment it completes (that's how status polling has always
  worked here) -- the folder system is purely organizational metadata on
  top of something already saved, not a separate "save" action. Filing
  something into a folder or giving it a title is just a PATCH.
*/

const LANGUAGES = ["python", "java", "cpp", "javascript", "c"];
const LANGUAGE_LABELS = { python: "Python", java: "Java", cpp: "C++", javascript: "JavaScript", c: "C" };

export default function CodeStudioPage() {
  const [mode, setMode] = useState("translate"); // "translate" | "solve" | "visualize" | "practice" | "dashboard"
  const [view, setView] = useState("working"); // "working" | "unfiled" | <folderId>

  // translate/solve inputs
  const [sourceLanguage, setSourceLanguage] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("java");
  const [sourceCode, setSourceCode] = useState("");
  const [problemStatement, setProblemStatement] = useState("");
  const [codeStyleProfileId, setCodeStyleProfileId] = useState("");
  const [styleProfiles, setStyleProfiles] = useState([]);
  const [conversionResult, setConversionResult] = useState(null);
  const [activeMapping, setActiveMapping] = useState(null);
  const [editing, setEditing] = useState(true);

  // visualize inputs
  const [visualizeSource, setVisualizeSource] = useState("");
  const [visualizeLanguage, setVisualizeLanguage] = useState("python");
  const [visualizationResult, setVisualizationResult] = useState(null);
  const [stepIndex, setStepIndex] = useState(0);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // folders + browsing
  const [folders, setFolders] = useState([]);
  const [savedItems, setSavedItems] = useState(null); // combined conversions + visualizations

  useEffect(() => {
    listCodeStyleProfiles().then(setStyleProfiles).catch(() => setStyleProfiles([]));
    refreshFolders();
  }, []);

  function refreshFolders() {
    listCodeWorkspaceFolders().then(setFolders).catch(() => setFolders([]));
  }

  function refreshSavedItems() {
    Promise.all([listConversions(), listVisualizations()]).then(([conversions, visualizations]) => {
      const tagged = [
        ...conversions.map((c) => ({ ...c, _kind: "conversion" })),
        ...visualizations.map((v) => ({ ...v, _kind: "visualization" })),
      ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setSavedItems(tagged);
    });
  }

  useEffect(() => {
    if (view !== "working") refreshSavedItems();
  }, [view]);

  const itemCounts = savedItemCounts(savedItems, folders);

  async function handleCreateFolder(name) {
    await createCodeWorkspaceFolder(name);
    refreshFolders();
  }

  async function handleDeleteFolder(folder) {
    await deleteCodeWorkspaceFolder(folder.id);
    refreshFolders();
    if (view === folder.id) setView("unfiled");
    refreshSavedItems();
  }

  function switchMode(next) {
    setMode(next);
    setError("");
    setActiveMapping(null);
    setEditing(true);
    setView("working");
  }

  async function handleSubmit() {
    setError("");
    setSubmitting(true);
    setActiveMapping(null);
    try {
      if (mode === "visualize") {
        const result = await visualizeCode({ sourceCode: visualizeSource, language: visualizeLanguage });
        setVisualizationResult(result);
        setStepIndex(0);
        if (result.status === "failed") setError(result.error_message || "Something went wrong.");
      } else {
        const result =
          mode === "translate"
            ? await translateCode({ sourceCode, sourceLanguage: sourceLanguage || null, targetLanguage, codeStyleProfileId })
            : await solveProblem({ problemStatement, targetLanguage, codeStyleProfileId });
        setConversionResult(result);
        setEditing(false);
        if (result.status === "failed") setError(result.error_message || "Something went wrong.");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not complete that request.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleVisualizeThis() {
    if (!conversionResult?.output_code) return;
    setVisualizeSource(conversionResult.output_code);
    setVisualizeLanguage(conversionResult.target_language);
    setVisualizationResult(null);
    setStepIndex(0);
    setMode("visualize");
    setView("working");
  }

  function handleSourceLineClick(lineNum) {
    if (!conversionResult?.mapping) return;
    const block = conversionResult.mapping.find((b) => lineNum >= b.source_lines[0] && lineNum <= b.source_lines[1]);
    setActiveMapping(block || null);
  }

  function handleOutputLineClick(lineNum) {
    if (!conversionResult?.mapping) return;
    const block = conversionResult.mapping.find((b) => lineNum >= b.output_lines[0] && lineNum <= b.output_lines[1]);
    setActiveMapping(block || null);
  }

  async function handleUpdateConversion(changes) {
    const updated = await updateConversion(conversionResult.id, changes);
    setConversionResult(updated);
    refreshFolders();
  }

  async function handleUpdateVisualization(changes) {
    const updated = await updateVisualization(visualizationResult.id, changes);
    setVisualizationResult(updated);
    refreshFolders();
  }

  function openSavedItem(item) {
    if (item._kind === "conversion") {
      setMode(item.mode); // "translate" | "solve"
      setConversionResult(item);
      setSourceCode(item.source_code || "");
      setProblemStatement(item.problem_statement || "");
      setTargetLanguage(item.target_language);
      setEditing(false);
      setActiveMapping(null);
    } else {
      setMode("visualize");
      setVisualizationResult(item);
      setVisualizeSource(item.source_code);
      setVisualizeLanguage(item.language);
      setStepIndex(0);
    }
    setView("working");
  }

  async function handleDeleteSavedItem(item, e) {
    e.stopPropagation();
    if (item._kind === "conversion") await deleteConversion(item.id);
    else await deleteVisualization(item.id);
    refreshSavedItems();
    refreshFolders();
  }

  const canSubmit =
    mode === "translate" ? sourceCode.trim().length > 0 :
    mode === "solve" ? problemStatement.trim().length > 0 :
    visualizeSource.trim().length > 0;

  const currentStep = visualizationResult?.trace?.[stepIndex] || null;

  return (
    <AppShell section="Code Studio" current={{ translate: "Translate", solve: "Solve", visualize: "Visualize", practice: "Practice", dashboard: "Dashboard" }[mode]}>
      <div className="page-head">
        <div>
          <div className="page-title">Code Studio</div>
          <div className="page-sub">Translate between languages, solve a new problem, or step through what code actually does.</div>
        </div>
      </div>

      <div className="studio-layout">
        <FolderSidebar
          folders={folders}
          activeView={view}
          onSelectView={setView}
          itemCounts={itemCounts}
          onCreateFolder={handleCreateFolder}
          onDeleteFolder={handleDeleteFolder}
        />

        <div className="studio-main">
          {view !== "working" ? (
            <SavedItemsList
              items={filterByView(savedItems, view)}
              onOpen={openSavedItem}
              onDelete={handleDeleteSavedItem}
            />
          ) : (
            <div className="conv-shell">
              <div className="conv-mode-bar">
                <button className={`mode-btn ${mode === "translate" ? "mode-btn-on" : ""}`} onClick={() => switchMode("translate")}>
                  <Icon name="swap" size={15} /> Translate
                </button>
                <button className={`mode-btn ${mode === "solve" ? "mode-btn-on" : ""}`} onClick={() => switchMode("solve")}>
                  <Icon name="wand" size={15} /> Solve
                </button>
                <button className={`mode-btn ${mode === "visualize" ? "mode-btn-on" : ""}`} onClick={() => switchMode("visualize")}>
                  <Icon name="eye" size={15} /> Visualize
                </button>
                <button className={`mode-btn ${mode === "practice" ? "mode-btn-on" : ""}`} onClick={() => switchMode("practice")}>
                  <Icon name="exams" size={15} /> Practice
                </button>
                <button className={`mode-btn ${mode === "dashboard" ? "mode-btn-on" : ""}`} onClick={() => switchMode("dashboard")}>
                  <Icon name="overview" size={15} /> Dashboard
                </button>
              </div>

              {mode === "dashboard" ? (
                <DashboardPane />
              ) : mode === "practice" ? (
                <PracticePane folders={folders} />
              ) : mode === "visualize" ? (
                <VisualizePane
                  source={visualizeSource}
                  setSource={setVisualizeSource}
                  language={visualizeLanguage}
                  setLanguage={setVisualizeLanguage}
                  result={visualizationResult}
                  stepIndex={stepIndex}
                  setStepIndex={setStepIndex}
                  currentStep={currentStep}
                  onUpdate={handleUpdateVisualization}
                  folders={folders}
                />
              ) : (
                <ConvertSolvePane
                  mode={mode}
                  sourceLanguage={sourceLanguage}
                  setSourceLanguage={setSourceLanguage}
                  targetLanguage={targetLanguage}
                  setTargetLanguage={setTargetLanguage}
                  sourceCode={sourceCode}
                  setSourceCode={setSourceCode}
                  problemStatement={problemStatement}
                  setProblemStatement={setProblemStatement}
                  codeStyleProfileId={codeStyleProfileId}
                  setCodeStyleProfileId={setCodeStyleProfileId}
                  styleProfiles={styleProfiles}
                  result={conversionResult}
                  editing={editing}
                  setEditing={setEditing}
                  activeMapping={activeMapping}
                  onSourceLineClick={handleSourceLineClick}
                  onOutputLineClick={handleOutputLineClick}
                  onVisualizeThis={handleVisualizeThis}
                  onUpdate={handleUpdateConversion}
                  folders={folders}
                />
              )}

              {mode !== "practice" && mode !== "dashboard" && (
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <Button
                    icon={<Icon name={mode === "translate" ? "swap" : mode === "solve" ? "wand" : "eye"} size={16} />}
                    onClick={handleSubmit}
                    disabled={!canSubmit || submitting}
                  >
                    {submitting ? "Working..." : mode === "translate" ? "Translate" : mode === "solve" ? "Solve" : "Trace"}
                  </Button>
                  {error && <div className="error-text">{error}</div>}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

/* ---------- helpers ---------- */

function filterByView(items, view) {
  if (!items) return [];
  if (view === "unfiled") return items.filter((i) => !i.folder_id);
  return items.filter((i) => i.folder_id === view);
}

function savedItemCounts(items, folders) {
  const counts = { unfiled: 0 };
  for (const f of folders) counts[f.id] = 0;
  if (items) {
    for (const item of items) {
      const key = item.folder_id || "unfiled";
      counts[key] = (counts[key] || 0) + 1;
    }
  }
  return counts;
}

function itemLabel(item) {
  if (item.title) return item.title;
  if (item._kind === "visualization") return `Trace: ${item.language}`;
  if (item.mode === "solve") return item.problem_statement?.slice(0, 60) || "Untitled solve";
  return item.source_code?.split("\n")[0]?.slice(0, 60) || "Untitled translation";
}

/* ---------- sub-components ---------- */

function SavedItemsList({ items, onOpen, onDelete }) {
  if (items.length === 0) {
    return (
      <div className="list-card">
        <div className="lib-empty">
          <div className="lib-empty-title">Nothing filed here yet</div>
          <div className="lib-empty-copy">
            Anything you translate, solve, or visualize is saved automatically. File it into a folder from
            the save controls once you have a result.
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="list-card">
      {items.map((item) => (
        <div className="saved-item-row" key={`${item._kind}-${item.id}`} onClick={() => onOpen(item)}>
          <Icon name={item._kind === "visualization" ? "eye" : item.mode === "solve" ? "wand" : "swap"} size={14} />
          <span className="saved-item-title">{itemLabel(item)}</span>
          {item.is_favorite && <Icon name="pin" size={12} style={{ color: "var(--amber)" }} />}
          <span className="saved-item-meta">{new Date(item.created_at).toLocaleDateString()}</span>
          <button className="mini-btn" onClick={(e) => onDelete(item, e)} title="Delete">
            <Icon name="trash" size={13} />
          </button>
        </div>
      ))}
    </div>
  );
}

function SaveControls({ item, onUpdate, folders }) {
  const [title, setTitle] = useState(item.title || "");

  return (
    <div className="save-controls">
      <input
        className="save-title-input"
        placeholder="Untitled -- click to name this"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onBlur={() => title !== (item.title || "") && onUpdate({ title })}
      />
      <select
        className="conv-select"
        value={item.folder_id || ""}
        onChange={(e) => onUpdate({ folder_id: e.target.value || null })}
      >
        <option value="">Unfiled</option>
        {folders.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
      </select>
      <button
        className="mini-btn"
        onClick={() => onUpdate({ is_favorite: !item.is_favorite })}
        title={item.is_favorite ? "Unpin" : "Pin"}
        style={{ color: item.is_favorite ? "var(--amber)" : undefined }}
      >
        <Icon name="pin" size={14} />
      </button>
    </div>
  );
}

function ConvertSolvePane({
  mode, sourceLanguage, setSourceLanguage, targetLanguage, setTargetLanguage,
  sourceCode, setSourceCode, problemStatement, setProblemStatement,
  codeStyleProfileId, setCodeStyleProfileId, styleProfiles,
  result, editing, setEditing, activeMapping, onSourceLineClick, onOutputLineClick,
  onVisualizeThis, onUpdate, folders,
}) {
  return (
    <div className="conv-panes">
      <div className="conv-pane card">
        <div className="conv-pane-head">
          <span className="conv-pane-title">{mode === "translate" ? "Source" : "Problem"}</span>
          {mode === "translate" && (
            <select className="conv-select" value={sourceLanguage} onChange={(e) => setSourceLanguage(e.target.value)}>
              <option value="">Auto-detect</option>
              {LANGUAGES.map((l) => <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>)}
            </select>
          )}
          {mode === "translate" && result?.status === "ready" && result.source_language && (
            <span className="hint">detected: {LANGUAGE_LABELS[result.source_language] || result.source_language}</span>
          )}
          {mode === "translate" && !editing && (
            <button className="mini-btn" style={{ marginLeft: "auto" }} onClick={() => setEditing(true)} title="Edit source">
              <Icon name="fileText" size={14} />
            </button>
          )}
        </div>

        {mode === "translate" ? (
          editing ? (
            <textarea className="conv-textarea" placeholder="Paste your source code here..." value={sourceCode}
              onChange={(e) => setSourceCode(e.target.value)} spellCheck={false} />
          ) : (
            <CodeLines code={sourceCode} activeRange={activeMapping?.source_lines} onLineClick={onSourceLineClick} />
          )
        ) : (
          <textarea className="conv-textarea"
            placeholder="Describe the problem you want solved, e.g. 'write a function that checks if a string is a palindrome'"
            value={problemStatement} onChange={(e) => setProblemStatement(e.target.value)} />
        )}
      </div>

      <div className="conv-pane card">
        <div className="conv-pane-head">
          <span className="conv-pane-title">Output</span>
          <select className="conv-select conv-select-right" value={codeStyleProfileId}
            onChange={(e) => setCodeStyleProfileId(e.target.value)} title="Coding style">
            <option value="">Default style</option>
            {styleProfiles.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
          <select className="conv-select" value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
            {LANGUAGES.map((l) => <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>)}
          </select>
        </div>

        {!result ? (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--faint)", fontSize: 13, minHeight: 320 }}>
            {mode === "translate" ? "Translated code will appear here" : "Your solution will appear here"}
          </div>
        ) : result.status === "generating" || result.status === "pending" ? (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", minHeight: 320 }}>
            <div className="progress" style={{ width: "60%" }}>
              <div className="progress-fill" style={{ width: "45%", animation: "chhaya-indeterminate 1.4s ease-in-out infinite" }} />
            </div>
          </div>
        ) : result.status === "failed" ? (
          <div style={{ padding: 18 }}>
            <div className="banner banner-danger" style={{ marginBottom: 0 }}>
              <Icon name="alertTriangle" size={18} />
              <div>
                <div className="banner-title">Could not generate output</div>
                <div className="banner-copy">{result.error_message}</div>
              </div>
            </div>
          </div>
        ) : (
          <CodeLines code={result.output_code} activeRange={activeMapping?.output_lines} onLineClick={onOutputLineClick} />
        )}

        {activeMapping?.description && <div className="conv-block-desc">{activeMapping.description}</div>}
        {result?.status === "ready" && result.explanation && (
          <div className="conv-foot"><div className="hint">{result.explanation}</div></div>
        )}
        {result?.status === "ready" && (
          <>
            <div style={{ padding: "10px 14px 0" }}>
              <Button variant="ghost" size="sm" icon={<Icon name="eye" size={14} />} onClick={onVisualizeThis}>
                Visualize this
              </Button>
            </div>
            <SaveControls item={result} onUpdate={onUpdate} folders={folders} />
          </>
        )}
      </div>
    </div>
  );
}

function VisualizePane({ source, setSource, language, setLanguage, result, stepIndex, setStepIndex, currentStep, onUpdate, folders }) {
  const totalSteps = result?.trace?.length || 0;

  return (
    <div className="conv-panes">
      <div className="conv-pane card">
        <div className="conv-pane-head">
          <span className="conv-pane-title">Code</span>
          <select className="conv-select conv-select-right" value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((l) => <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>)}
          </select>
        </div>
        {result?.status === "ready" ? (
          <CodeLines code={source} activeRange={currentStep && currentStep.line > 0 ? [currentStep.line, currentStep.line] : null} onLineClick={() => {}} />
        ) : (
          <textarea className="conv-textarea" placeholder="Paste code to trace, or use 'Visualize this' from Translate/Solve..."
            value={source} onChange={(e) => setSource(e.target.value)} spellCheck={false} />
        )}
      </div>

      <div className="conv-pane card">
        <div className="conv-pane-head">
          <span className="conv-pane-title">Trace</span>
        </div>

        {!result ? (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--faint)", fontSize: 13, minHeight: 200 }}>
            Step-by-step execution will appear here
          </div>
        ) : result.status === "generating" || result.status === "pending" ? (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", minHeight: 200 }}>
            <div className="progress" style={{ width: "60%" }}>
              <div className="progress-fill" style={{ width: "45%", animation: "chhaya-indeterminate 1.4s ease-in-out infinite" }} />
            </div>
          </div>
        ) : result.status === "failed" ? (
          <div style={{ padding: 18 }}>
            <div className="banner banner-danger" style={{ marginBottom: 0 }}>
              <Icon name="alertTriangle" size={18} />
              <div>
                <div className="banner-title">Could not generate a trace</div>
                <div className="banner-copy">{result.error_message}</div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="stepper-controls">
              <button className="mini-btn" disabled={stepIndex === 0} onClick={() => setStepIndex((i) => Math.max(0, i - 1))}>
                <Icon name="chevronDown" size={14} style={{ transform: "rotate(90deg)" }} />
              </button>
              <span className="stepper-count">Step {stepIndex + 1} of {totalSteps}</span>
              <button className="mini-btn" disabled={stepIndex >= totalSteps - 1} onClick={() => setStepIndex((i) => Math.min(totalSteps - 1, i + 1))}>
                <Icon name="chevronDown" size={14} style={{ transform: "rotate(-90deg)" }} />
              </button>
            </div>
            <VariableWatchTable step={currentStep} />
            {result.explanation && <div className="conv-foot"><div className="hint">{result.explanation}</div></div>}
          </>
        )}

        {result?.status === "ready" && <SaveControls item={result} onUpdate={onUpdate} folders={folders} />}
      </div>
    </div>
  );
}

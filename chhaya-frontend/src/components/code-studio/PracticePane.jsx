import { useEffect, useRef, useState } from "react";
import Button from "../ui/Button";
import Badge from "../ui/Badge";
import Icon from "../icons/Icon";
import { suggestProblems, startAttempt, submitAttempt } from "../../api/practice";

/*
  Code Studio's Practice tab: pick a folder + difficulty, get problems
  matched to the work already saved in that folder, solve one against a
  timer, submit for review.

  THE TIMER DISPLAY IS DERIVED FROM THE SERVER'S started_at, not counted
  locally. The ticking number below is recomputed each second as
  (now - attempt.started_at), so refreshing the page or leaving the tab
  doesn't reset or pause it -- and the backend recomputes elapsed time
  independently on submit anyway (see practice_service.submit_attempt),
  so what's recorded never depends on the browser at all.
*/

const LANGUAGES = ["python", "java", "cpp", "javascript", "c"];
const LANGUAGE_LABELS = { python: "Python", java: "Java", cpp: "C++", javascript: "JavaScript", c: "C" };
const DIFFICULTIES = ["easy", "medium", "hard"];

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function PracticePane({ folders }) {
  const [folderId, setFolderId] = useState("");
  const [difficulty, setDifficulty] = useState("easy");
  const [suggestions, setSuggestions] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [error, setError] = useState("");

  const [attempt, setAttempt] = useState(null);
  const [activeProblem, setActiveProblem] = useState(null);
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [elapsed, setElapsed] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [verdict, setVerdict] = useState(null);

  const timerRef = useRef(null);

  // Ticks the display off the server's started_at. Cleared whenever the
  // attempt ends or the component unmounts, so no stray interval survives.
  useEffect(() => {
    if (!attempt || verdict) {
      clearInterval(timerRef.current);
      return;
    }
    const startedAt = new Date(attempt.started_at).getTime();
    const tick = () => setElapsed(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)));
    tick();
    timerRef.current = setInterval(tick, 1000);
    return () => clearInterval(timerRef.current);
  }, [attempt, verdict]);

  async function handleSuggest() {
    if (!folderId) {
      setError("Pick a folder first -- suggestions are based on the work saved in it.");
      return;
    }
    setError("");
    setLoadingSuggestions(true);
    try {
      const results = await suggestProblems({ folderId, difficulty, limit: 5 });
      setSuggestions(results);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load suggestions.");
    } finally {
      setLoadingSuggestions(false);
    }
  }

  async function handleStart(problem) {
    setError("");
    try {
      const created = await startAttempt({ problemId: problem.id, folderId });
      setAttempt(created);
      setActiveProblem(problem);
      setVerdict(null);
      setCode("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not start that problem.");
    }
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError("");
    try {
      const result = await submitAttempt(attempt.id, { submittedCode: code, language });
      setVerdict(result);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not submit.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleBackToList() {
    setAttempt(null);
    setActiveProblem(null);
    setVerdict(null);
    setCode("");
    setElapsed(0);
  }

  // ---------- solving view ----------
  if (attempt && activeProblem) {
    return (
      <div className="conv-panes">
        <div className="conv-pane card">
          <div className="timer-bar">
            <Icon name="wand" size={15} />
            <span className="timer-value">{formatElapsed(verdict?.seconds_taken ?? elapsed)}</span>
            <Badge className={`diff-${activeProblem.difficulty}`}>{activeProblem.difficulty}</Badge>
            <button className="mini-btn" style={{ marginLeft: "auto" }} onClick={handleBackToList} title="Back to problems">
              <Icon name="chevronDown" size={14} style={{ transform: "rotate(90deg)" }} />
            </button>
          </div>
          <div style={{ padding: 16, overflowY: "auto", maxHeight: 460 }}>
            <div className="problem-card-title" style={{ marginBottom: 10 }}>{activeProblem.title}</div>
            {/*
              The dataset stores problem statements as HTML. Rendering it
              is what makes examples/constraints look like a real problem
              page -- the .problem-content CSS styles the <pre>/<code>/<ul>
              tags it contains.
            */}
            <div
              className="problem-content"
              dangerouslySetInnerHTML={{ __html: activeProblem.description }}
            />
          </div>
        </div>

        <div className="conv-pane card">
          <div className="conv-pane-head">
            <span className="conv-pane-title">Your solution</span>
            <select
              className="conv-select conv-select-right"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={!!verdict}
            >
              {LANGUAGES.map((l) => <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>)}
            </select>
          </div>

          {verdict ? (
            <div style={{ padding: 16, overflowY: "auto" }}>
              <div className={`verdict-banner ${verdict.is_correct ? "verdict-ok" : "verdict-bad"}`}>
                <Icon name={verdict.is_correct ? "check" : "alertTriangle"} size={20} />
                <div>
                  <div className="verdict-title">
                    {verdict.is_correct === null
                      ? "Saved, but not reviewed"
                      : verdict.is_correct
                      ? "Correct"
                      : "Not quite"}
                  </div>
                  <div className="verdict-body">{verdict.feedback}</div>
                  <div className="complexity-row">
                    {verdict.time_complexity && <Badge variant="iris">Time {verdict.time_complexity}</Badge>}
                    {verdict.space_complexity && <Badge variant="plum">Space {verdict.space_complexity}</Badge>}
                    <Badge>Solved in {formatElapsed(verdict.seconds_taken || 0)}</Badge>
                  </div>
                </div>
              </div>
              <Button variant="ghost" onClick={handleBackToList}>Back to problems</Button>
            </div>
          ) : (
            <>
              <textarea
                className="conv-textarea"
                placeholder="Write your solution here..."
                value={code}
                onChange={(e) => setCode(e.target.value)}
                spellCheck={false}
              />
              <div className="save-controls">
                <Button icon={<Icon name="check" size={15} />} onClick={handleSubmit} disabled={submitting || !code.trim()}>
                  {submitting ? "Reviewing..." : "Submit"}
                </Button>
                {error && <div className="error-text">{error}</div>}
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  // ---------- problem picker view ----------
  return (
    <div className="card">
      <div className="card-head">
        <span className="card-title">Practice</span>
        <span className="card-note">Problems matched to what you've been working on</span>
      </div>

      <div className="practice-setup">
        <div className="field" style={{ flex: 1, minWidth: 180 }}>
          <div className="label">Based on folder</div>
          <select className="select" value={folderId} onChange={(e) => setFolderId(e.target.value)}>
            <option value="">Choose a folder...</option>
            {folders.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
        <div className="field" style={{ minWidth: 140 }}>
          <div className="label">Difficulty</div>
          <select className="select" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <Button icon={<Icon name="search" size={15} />} onClick={handleSuggest} disabled={loadingSuggestions}>
          {loadingSuggestions ? "Finding..." : "Find problems"}
        </Button>
      </div>

      {error && <div className="error-text" style={{ padding: "0 14px 12px" }}>{error}</div>}

      <div style={{ padding: "0 14px 14px" }}>
        {suggestions === null ? (
          <div className="hint">
            Pick a folder of saved work and a difficulty, and Chhaya will find problems that exercise the
            same concepts.
          </div>
        ) : suggestions.length === 0 ? (
          <div className="hint">No matching problems found. Try a different difficulty.</div>
        ) : (
          suggestions.map(({ problem, reason }) => (
            <div className="problem-card" key={problem.id}>
              <div className="problem-card-head">
                <span className="problem-card-title">{problem.title}</span>
                <Badge className={`diff-${problem.difficulty}`}>{problem.difficulty}</Badge>
              </div>
              {reason && <div className="problem-reason">{reason}</div>}
              <Button size="sm" icon={<Icon name="wand" size={14} />} onClick={() => handleStart(problem)}>
                Start
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { TextField } from "../../components/ui/Field";
import { listExamPapers } from "../../api/examPapers";
import { createLikelyQuestionSet } from "../../api/likelyQuestions";

export default function CreateLikelyQuestionsPage() {
  const navigate = useNavigate();
  const [papers, setPapers] = useState(null); const [title, setTitle] = useState("Likely exam practice questions");
  const [course, setCourse] = useState(""); const [selected, setSelected] = useState([]); const [questionCount, setQuestionCount] = useState(8);
  const [error, setError] = useState(""); const [submitting, setSubmitting] = useState(false);
  useEffect(() => { listExamPapers().then(setPapers).catch(() => setPapers([])); }, []);
  const ready = (papers || []).filter((paper) => paper.status === "ready" && paper.extracted_text);
  function toggle(id) { setSelected((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]); }
  async function submit(event) { event.preventDefault(); if (!selected.length) return setError("Select at least one OCR-ready paper."); setSubmitting(true); setError(""); try { const result = await createLikelyQuestionSet({ title, course, examPaperIds: selected, questionCount }); navigate(`/likely-questions/${result.id}`); } catch (err) { setError(err.response?.data?.detail || "Could not generate likely questions."); setSubmitting(false); } }
  return <AppShell section="Likely questions" current="Generate"><div className="page-head"><div><div className="page-title">Generate likely questions</div><div className="page-sub">Gemini analyses patterns from selected past papers. Predictions are for practice, not guarantees.</div></div></div><form onSubmit={submit} className="card" style={{ maxWidth: 680 }}><div className="form-grid"><TextField label="Set title" value={title} onChange={(event) => setTitle(event.target.value)} required /><TextField label="Course (optional)" value={course} onChange={(event) => setCourse(event.target.value)} /><div className="field"><div className="label">Number of practice questions</div><input type="number" min="3" max="20" value={questionCount} onChange={(event) => setQuestionCount(Number(event.target.value))} /></div><div className="field"><div className="label">OCR-ready past papers</div>{papers === null ? <div className="hint">Loading papers…</div> : ready.length === 0 ? <div className="hint">No ready papers found. Upload a paper and wait for its OCR status to become Ready.</div> : ready.map((paper) => <label key={paper.id} className="pick-row" style={{ cursor: "pointer" }}><input type="checkbox" checked={selected.includes(paper.id)} onChange={() => toggle(paper.id)} /><div style={{ marginLeft: 10 }}><div className="pick-name">{paper.title}</div><div className="pick-sub">{paper.course || "No course"}</div></div></label>)}</div></div><div className="form-foot"><Button type="submit" disabled={submitting || !selected.length}>{submitting ? "Analysing papers…" : "Analyse and generate"}</Button><Button type="button" variant="ghost" onClick={() => navigate("/likely-questions")}>Cancel</Button>{error && <div className="error-text">{error}</div>}</div></form></AppShell>;
}

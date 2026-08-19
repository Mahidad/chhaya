import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { getQuizResults, retryQuiz } from "../../api/quizzes";


// ── status display ─────────────────────────────────────────────────────────

const PASS_STATUS_CONFIG = {
  good_job:           { label: "Good job!",          color: "var(--ok)",     bg: "var(--ok-soft)" },
  required_retake:    { label: "Required retake",    color: "var(--amber)",  bg: "rgba(245,158,11,0.08)" },
  need_urgent_retake: { label: "Need urgent retake", color: "var(--danger)", bg: "rgba(239,68,68,0.08)" },
};


export default function QuizResultsPage() {
  const { quizId } = useParams();
  const navigate = useNavigate();

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    getQuizResults(quizId)
      .then(setResult)
      .catch(() => setError("Could not load results. Has this quiz been graded?"));
  }, [quizId]);

  async function handleRetry() {
    setRetrying(true);
    try {
      const newQuiz = await retryQuiz(quizId);
      navigate(`/quizzes/${newQuiz.id}`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || "Could not create a retry attempt.");
      setRetrying(false);
    }
  }

  // ── loading / error ────────────────────────────────────────────────────────

  if (!result && !error) {
    return (
      <AppShell section="Learning" current="Quizzes">
        <div className="card card-pad" style={{ color: "var(--muted)" }}>Loading results…</div>
      </AppShell>
    );
  }

  if (error && !result) {
    return (
      <AppShell section="Learning" current="Quizzes">
        <div className="banner banner-danger">{error}</div>
        <div style={{ marginTop: 16 }}>
          <Button variant="ghost" onClick={() => navigate("/quizzes")}>Back to quizzes</Button>
        </div>
      </AppShell>
    );
  }

  const statusConfig = PASS_STATUS_CONFIG[result.pass_status] || {
    label: result.pass_status, color: "var(--muted)", bg: "var(--surface)",
  };

  return (
    <AppShell section="Learning" current="Quizzes">
      {/* Page header */}
      <div className="page-head">
        <div>
          <div className="page-title">{result.title}</div>
          <div className="page-sub">
            Attempt #{result.attempt_number} · {result.difficulty} · {result.num_questions} questions
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Button variant="ghost" onClick={() => navigate("/quizzes")}>
            All quizzes
          </Button>
          <Button variant="primary" disabled={retrying} onClick={handleRetry}>
            {retrying ? "Creating retry…" : "Retry this quiz"}
          </Button>
        </div>
      </div>

      {error && <div className="banner banner-danger" style={{ marginBottom: 16 }}>{error}</div>}

      {/* Score summary card */}
      <div className="card card-pad" style={{ marginBottom: 24 }}>
        {/* Pass status banner */}
        <div style={{
          background: statusConfig.bg,
          color: statusConfig.color,
          borderRadius: 8,
          padding: "12px 16px",
          fontWeight: 700,
          fontSize: 16,
          marginBottom: 20,
        }}>
          {statusConfig.label}
        </div>

        {/* Score stats */}
        <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
          <div>
            <div className="hint">Score</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "var(--ink)" }}>
              {result.total_score} / {result.max_score}
            </div>
          </div>
          <div>
            <div className="hint">Percentage</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: statusConfig.color }}>
              {result.percentage?.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="hint">Difficulty</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: "var(--ink)", textTransform: "capitalize" }}>
              {result.difficulty}
            </div>
          </div>
        </div>
      </div>

      {/* Per-question breakdown */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 15, color: "var(--ink)", marginBottom: 12 }}>
          Question-by-question breakdown
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {result.graded_answers.map((ga, index) => {
            const gotFull = ga.marks_obtained === ga.max_marks;
            const gotNone = ga.marks_obtained === 0;
            const scoreColor = gotFull ? "var(--ok)" : gotNone ? "var(--danger)" : "var(--amber)";

            return (
              <div key={ga.question_id} className="card card-pad">
                {/* Question header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 10 }}>
                  <div style={{ fontWeight: 700, color: "var(--ink)", flex: 1 }}>
                    Q{index + 1}. {ga.question_text}
                  </div>
                  <div style={{
                    fontWeight: 700,
                    fontSize: 15,
                    color: scoreColor,
                    whiteSpace: "nowrap",
                  }}>
                    {ga.marks_obtained} / {ga.max_marks}
                  </div>
                </div>

                {/* Student's answer */}
                <div style={{ marginBottom: 10 }}>
                  <div className="hint" style={{ marginBottom: 4 }}>Your answer</div>
                  <div style={{
                    background: "var(--surface)",
                    border: "1px solid var(--line)",
                    borderRadius: 6,
                    padding: "8px 12px",
                    fontSize: 14,
                    color: "var(--ink)",
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.6,
                  }}>
                    {ga.answer_text || <span style={{ color: "var(--faint)" }}>No answer given</span>}
                  </div>
                </div>

                {/* Gemini feedback */}
                <div>
                  <div className="hint" style={{ marginBottom: 4 }}>Feedback</div>
                  <div style={{
                    background: gotFull ? "var(--ok-soft)" : "var(--surface)",
                    border: `1px solid ${gotFull ? "var(--ok)" : "var(--line)"}`,
                    borderRadius: 6,
                    padding: "8px 12px",
                    fontSize: 14,
                    color: "var(--ink)",
                    lineHeight: 1.6,
                  }}>
                    {ga.feedback}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom actions */}
      <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
        <Button variant="primary" disabled={retrying} onClick={handleRetry}>
          {retrying ? "Creating retry…" : "Retry this quiz"}
        </Button>
        <Button variant="ghost" onClick={() => navigate("/quizzes")}>
          Back to all quizzes
        </Button>
      </div>
    </AppShell>
  );
}

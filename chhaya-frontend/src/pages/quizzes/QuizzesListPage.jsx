import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { listQuizzes, deleteQuiz, retryQuiz } from "../../api/quizzes";


// ── status display config ────────────────────────────────────────────────────

// Urgency sort order (lower number = shown first)
const URGENCY_ORDER = {
  need_urgent_retake: 0,
  required_retake:    1,
  good_job:           2,
};

const PASS_STATUS_LABELS = {
  need_urgent_retake: { label: "Need urgent retake", color: "var(--danger)" },
  required_retake:    { label: "Required retake",    color: "var(--amber)" },
  good_job:           { label: "Good job",           color: "var(--ok)" },
};

const STATUS_STYLES = {
  not_started:   { label: "Not started",    color: "var(--faint)" },
  in_progress:   { label: "In progress",    color: "var(--amber)" },
  submitted:     { label: "Submitted",      color: "var(--iris)" },
  auto_submitted:{ label: "Auto-submitted", color: "var(--iris)" },
};


// ── sort function ─────────────────────────────────────────────────────────────

function sortQuizzes(quizzes) {
  return [...quizzes].sort((a, b) => {
    // 1. Graded quizzes come first, sorted by urgency
    const aUrgency = a.pass_status !== null ? URGENCY_ORDER[a.pass_status] ?? 99 : 99;
    const bUrgency = b.pass_status !== null ? URGENCY_ORDER[b.pass_status] ?? 99 : 99;
    if (aUrgency !== bUrgency) return aUrgency - bUrgency;

    // 2. Within same urgency/topic, sort by chapter then attempt number
    if (a.chapter_id !== b.chapter_id) return a.chapter_id.localeCompare(b.chapter_id);
    return a.attempt_number - b.attempt_number;
  });
}


// ── component ─────────────────────────────────────────────────────────────────

export default function QuizzesListPage() {
  const navigate = useNavigate();
  const [quizzes, setQuizzes] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null); // tracks which quiz is being acted on

  async function loadQuizzes() {
    setError("");
    try {
      const data = await listQuizzes();
      setQuizzes(data);
    } catch {
      setError("Could not load quizzes. Is the backend running?");
    }
  }

  useEffect(() => {
    loadQuizzes();
  }, []);

  async function handleDelete(quizId) {
    if (!window.confirm("Delete this quiz attempt? Other attempts for the same topic will not be affected.")) return;
    setBusyId(quizId);
    try {
      await deleteQuiz(quizId);
      await loadQuizzes();
    } catch {
      setError("Could not delete the quiz.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleRetry(quizId) {
    setBusyId(quizId);
    try {
      const newQuiz = await retryQuiz(quizId);
      // Navigate straight to the new quiz session
      navigate(`/quizzes/${newQuiz.id}`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || "Could not create a retry. Make sure your notes still have enough content.");
      setBusyId(null);
    }
  }

  const sorted = quizzes ? sortQuizzes(quizzes) : [];

  return (
    <AppShell section="Learning" current="Quizzes">
      <div className="page-head">
        <div>
          <div className="page-title">Quizzes</div>
          <div className="page-sub">
            Generate quizzes from your notes, take them timed, and track your progress over time.
          </div>
        </div>
        <Button
          variant="primary"
          icon={<Icon name="plus" size={16} />}
          onClick={() => navigate("/quizzes/new")}
        >
          Generate quiz
        </Button>
      </div>

      {error && <div className="banner banner-danger">{error}</div>}

      {quizzes === null ? (
        <div className="card card-pad" style={{ color: "var(--muted)" }}>Loading quizzes…</div>
      ) : quizzes.length === 0 ? (
        <div className="card card-pad" style={{ color: "var(--muted)" }}>
          No quizzes yet. Click "Generate quiz" to create one from your notes.
        </div>
      ) : (
        <div className="list-card">
          {sorted.map((quiz) => {
            const isBusy = busyId === quiz.id;

            // Pick status display: graded quizzes show pass_status, others show quiz status
            const isGraded = quiz.pass_status !== null;
            const passInfo = PASS_STATUS_LABELS[quiz.pass_status];
            const statusInfo = STATUS_STYLES[quiz.status] || { label: quiz.status, color: "var(--faint)" };

            return (
              <div
                key={quiz.id}
                className="prow"
                style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}
              >
                {/* Title and meta */}
                <div style={{ flex: "1 1 220px" }}>
                  <div style={{ fontWeight: 700, color: "var(--ink)" }}>{quiz.title}</div>
                  <div className="hint" style={{ marginTop: 4 }}>
                    {quiz.num_questions}Q · {quiz.marks_per_question}M each · {quiz.duration_minutes} min
                    {" · "}Attempt #{quiz.attempt_number}
                    {/* Show score if graded */}
                    {isGraded && (
                      <span style={{ marginLeft: 8, fontWeight: 600, color: "var(--ink)" }}>
                        · {quiz.total_score}/{quiz.max_score} ({quiz.percentage?.toFixed(1)}%)
                      </span>
                    )}
                  </div>
                </div>

                {/* Status badge */}
                {isGraded ? (
                  <span style={{ fontSize: 12, fontWeight: 600, color: passInfo?.color, whiteSpace: "nowrap" }}>
                    {passInfo?.label || quiz.pass_status}
                  </span>
                ) : (
                  <span style={{ fontSize: 12, fontWeight: 600, color: statusInfo.color, whiteSpace: "nowrap" }}>
                    {statusInfo.label}
                  </span>
                )}

                {/* Actions */}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>

                  {/* View/Start/Grade button */}
                  {isGraded ? (
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/quizzes/${quiz.id}/results`)}>
                      View results
                    </Button>
                  ) : (quiz.status === "submitted" || quiz.status === "auto_submitted") ? (
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/quizzes/${quiz.id}`)}>
                      Grade quiz
                    </Button>
                  ) : (
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/quizzes/${quiz.id}`)}>
                      {quiz.status === "not_started" ? "Start" : "Continue"}
                    </Button>
                  )}

                  {/* Retry — only available after grading */}
                  {isGraded && (
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={isBusy}
                      onClick={() => handleRetry(quiz.id)}
                    >
                      {isBusy ? "Creating…" : "Retry"}
                    </Button>
                  )}

                  {/* Delete */}
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={isBusy}
                    onClick={() => handleDelete(quiz.id)}
                    icon={<Icon name="trash" size={14} />}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}

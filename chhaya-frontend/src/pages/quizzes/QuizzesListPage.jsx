import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { listQuizzes, deleteQuiz } from "../../api/quizzes";


// Map status values to a readable label and color
const STATUS_STYLES = {
  not_started: { label: "Not started", color: "var(--faint)" },
  in_progress:  { label: "In progress",  color: "var(--amber)" },
  submitted:    { label: "Submitted",    color: "var(--ok)" },
  auto_submitted: { label: "Auto-submitted", color: "var(--iris)" },
};


export default function QuizzesListPage() {
  const navigate = useNavigate();
  const [quizzes, setQuizzes] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

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
    if (!window.confirm("Delete this quiz and all its questions?")) return;
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

  return (
    <AppShell section="Learning" current="Quizzes">
      <div className="page-head">
        <div>
          <div className="page-title">Quizzes</div>
          <div className="page-sub">Generate quizzes from your notes and take them with a timer.</div>
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
        <div className="card card-pad" style={{ color: "var(--muted)" }}>Loading quizzes...</div>
      ) : quizzes.length === 0 ? (
        <div className="card card-pad" style={{ color: "var(--muted)" }}>
          No quizzes yet. Click "Generate quiz" to create one from your notes.
        </div>
      ) : (
        <div className="list-card">
          {quizzes.map((quiz) => {
            const statusStyle = STATUS_STYLES[quiz.status] || { label: quiz.status, color: "var(--faint)" };
            return (
              <div className="prow" key={quiz.id} style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                {/* Title and meta */}
                <div style={{ flex: "1 1 220px" }}>
                  <div style={{ fontWeight: 700, color: "var(--ink)" }}>{quiz.title}</div>
                  <div className="hint" style={{ marginTop: 4 }}>
                    {quiz.num_questions} questions · {quiz.marks_per_question} marks each · {quiz.duration_minutes} min
                    {" · "}Attempt #{quiz.attempt_number}
                  </div>
                </div>

                {/* Status badge */}
                <span style={{ fontSize: 12, fontWeight: 600, color: statusStyle.color, whiteSpace: "nowrap" }}>
                  {statusStyle.label}
                </span>

                {/* Actions */}
                <div style={{ display: "flex", gap: 8 }}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/quizzes/${quiz.id}`)}
                  >
                    {quiz.status === "not_started" ? "Start" : "View"}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={busyId === quiz.id}
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

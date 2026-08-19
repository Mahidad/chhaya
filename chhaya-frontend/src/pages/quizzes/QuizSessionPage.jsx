import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { getQuizDetail, startQuiz, submitQuiz } from "../../api/quizzes";


// ── timer helpers ─────────────────────────────────────────────────────────────

/** How many whole seconds are left until the deadline. */
function secondsLeft(endsAt) {
  const diff = Math.floor((new Date(endsAt) - Date.now()) / 1000);
  return Math.max(0, diff);
}

/** Format seconds as MM:SS */
function formatCountdown(totalSeconds) {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}


// ── component ─────────────────────────────────────────────────────────────────

export default function QuizSessionPage() {
  const { quizId } = useParams();
  const navigate = useNavigate();

  // Quiz data from the backend
  const [quiz, setQuiz] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState("");

  // Answers: keyed by question id → answer text
  const [answers, setAnswers] = useState({});

  // Timer state — only active after the quiz is started
  const [endsAt, setEndsAt] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const timerRef = useRef(null);

  // UI phase: "setup" | "active" | "done"
  const [phase, setPhase] = useState("setup");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);  // { status, submitted_at }


  // ── load quiz on mount ──────────────────────────────────────────────────────

  useEffect(() => {
    async function load() {
      try {
        const data = await getQuizDetail(quizId);
        setQuiz(data);
        setQuestions(data.questions);

        // If the quiz is already in progress (page refresh scenario),
        // jump straight to active phase and restore the timer
        if (data.status === "in_progress" && data.ends_at) {
          setEndsAt(data.ends_at);
          setPhase("active");
        }

        // If already submitted, go straight to done
        if (data.status === "submitted" || data.status === "auto_submitted") {
          setResult({ status: data.status, submitted_at: data.submitted_at });
          setPhase("done");
        }
      } catch {
        setError("Could not load the quiz. Is the backend running?");
      }
    }
    load();
  }, [quizId]);


  // ── countdown ticker ────────────────────────────────────────────────────────

  useEffect(() => {
    if (!endsAt || phase !== "active") return;

    // Tick immediately so the display doesn't lag by 1 second
    setTimeLeft(secondsLeft(endsAt));

    timerRef.current = setInterval(() => {
      const remaining = secondsLeft(endsAt);
      setTimeLeft(remaining);

      // Auto-submit when timer hits zero
      if (remaining === 0) {
        clearInterval(timerRef.current);
        handleSubmit(true); // true = auto-submit
      }
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, [endsAt, phase]);


  // ── actions ─────────────────────────────────────────────────────────────────

  async function handleStart() {
    setError("");
    try {
      const data = await startQuiz(quizId);
      setEndsAt(data.ends_at);
      setQuiz((prev) => ({ ...prev, status: "in_progress", ends_at: data.ends_at }));
      setPhase("active");
    } catch {
      setError("Could not start the quiz. Please try again.");
    }
  }

  async function handleSubmit(isAutoSubmit = false) {
    if (submitting) return;
    setSubmitting(true);
    clearInterval(timerRef.current);

    // Build the answers list
    const answersList = questions.map((q) => ({
      question_id: q.id,
      answer_text: answers[q.id] || "",
    }));

    try {
      const data = await submitQuiz(quizId, answersList);
      setResult(data);
      setPhase("done");
    } catch {
      setError("Could not submit the quiz. Please try again.");
      setSubmitting(false);
      // If it was an auto-submit that failed, still show as done so the
      // student isn't stuck on a blank form
      if (isAutoSubmit) setPhase("done");
    }
  }


  // ── render helpers ───────────────────────────────────────────────────────────

  if (!quiz && !error) {
    return (
      <AppShell section="Learning" current="Quizzes">
        <div className="card card-pad" style={{ color: "var(--muted)" }}>Loading quiz...</div>
      </AppShell>
    );
  }

  if (error && !quiz) {
    return (
      <AppShell section="Learning" current="Quizzes">
        <div className="banner banner-danger">{error}</div>
      </AppShell>
    );
  }

  const totalMarks = quiz.num_questions * quiz.marks_per_question;


  // ── PHASE: setup (not started yet) ──────────────────────────────────────────

  if (phase === "setup") {
    return (
      <AppShell section="Learning" current="Quizzes">
        <div className="page-head">
          <div>
            <div className="page-title">{quiz.title}</div>
            <div className="page-sub">Review the details, then click Start when you are ready.</div>
          </div>
        </div>

        <div className="card card-pad" style={{ maxWidth: 480 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="prow" style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Questions</span>
              <span style={{ fontWeight: 600 }}>{quiz.num_questions}</span>
            </div>
            <div className="prow" style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Marks per question</span>
              <span style={{ fontWeight: 600 }}>{quiz.marks_per_question}</span>
            </div>
            <div className="prow" style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Total marks</span>
              <span style={{ fontWeight: 600 }}>{totalMarks}</span>
            </div>
            <div className="prow" style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Difficulty</span>
              <span style={{ fontWeight: 600, textTransform: "capitalize" }}>{quiz.difficulty}</span>
            </div>
            <div className="prow" style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Time limit</span>
              <span style={{ fontWeight: 600 }}>{quiz.duration_minutes} minutes</span>
            </div>
            <div className="prow" style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Attempt</span>
              <span style={{ fontWeight: 600 }}>#{quiz.attempt_number}</span>
            </div>
          </div>

          <div className="hint" style={{ marginTop: 16 }}>
            Once you click Start, the timer begins immediately and cannot be paused.
            The quiz auto-submits when time runs out.
          </div>

          {error && <div className="banner banner-danger" style={{ marginTop: 12 }}>{error}</div>}

          <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
            <Button variant="primary" onClick={handleStart}>
              Start quiz
            </Button>
            <Button variant="ghost" onClick={() => navigate("/quizzes")}>
              Back
            </Button>
          </div>
        </div>
      </AppShell>
    );
  }


  // ── PHASE: done (submitted) ──────────────────────────────────────────────────

  if (phase === "done") {
    const wasAuto = result?.status === "auto_submitted";
    return (
      <AppShell section="Learning" current="Quizzes">
        <div className="page-head">
          <div className="page-title">Quiz submitted</div>
        </div>

        <div className="card card-pad" style={{ maxWidth: 480 }}>
          {wasAuto ? (
            <div className="banner banner-danger" style={{ marginBottom: 16 }}>
              Time ran out — your answers were automatically submitted.
            </div>
          ) : (
            <div className="banner" style={{ marginBottom: 16, background: "var(--ok-soft)", color: "var(--ok)", border: "1px solid var(--ok)" }}>
              Submitted successfully!
            </div>
          )}

          <div style={{ color: "var(--muted)", marginBottom: 20 }}>
            Your answers have been saved. Feature 2 (grading) will evaluate them.
          </div>

          <Button variant="primary" onClick={() => navigate("/quizzes")}>
            Back to quizzes
          </Button>
        </div>
      </AppShell>
    );
  }


  // ── PHASE: active (quiz in progress) ────────────────────────────────────────

  const isAlmostOut = timeLeft !== null && timeLeft <= 60;

  return (
    <AppShell section="Learning" current="Quizzes">
      {/* Sticky header with timer */}
      <div className="page-head" style={{ position: "sticky", top: 0, background: "var(--canvas)", zIndex: 10, paddingBottom: 12 }}>
        <div>
          <div className="page-title">{quiz.title}</div>
          <div className="page-sub">Answer all questions and submit before time runs out.</div>
        </div>
        {/* Countdown timer */}
        <div style={{
          fontSize: 28,
          fontWeight: 700,
          color: isAlmostOut ? "var(--danger)" : "var(--primary)",
          fontVariantNumeric: "tabular-nums",
          minWidth: 80,
          textAlign: "right",
        }}>
          {timeLeft !== null ? formatCountdown(timeLeft) : "--:--"}
        </div>
      </div>

      {error && <div className="banner banner-danger" style={{ marginBottom: 16 }}>{error}</div>}

      {/* Questions */}
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        {questions.map((q, index) => (
          <div key={q.id} className="card card-pad">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
              <span style={{ fontWeight: 700, color: "var(--ink)" }}>
                Q{index + 1}. {q.question_text}
              </span>
              <span className="hint" style={{ whiteSpace: "nowrap", marginLeft: 12 }}>
                {q.marks} mark{q.marks === 1 ? "" : "s"}
              </span>
            </div>
            <textarea
              placeholder="Type your answer here…"
              value={answers[q.id] || ""}
              onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
              rows={4}
              style={{
                width: "100%",
                resize: "vertical",
                border: "1px solid var(--line)",
                borderRadius: 6,
                padding: "10px 12px",
                background: "var(--surface)",
                fontSize: 14,
                lineHeight: 1.6,
                color: "var(--ink)",
                outline: "none",
                fontFamily: "inherit",
              }}
            />
          </div>
        ))}
      </div>

      {/* Submit button */}
      <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
        <Button
          variant="primary"
          disabled={submitting}
          onClick={() => handleSubmit(false)}
        >
          {submitting ? "Submitting…" : "Submit quiz"}
        </Button>
      </div>
    </AppShell>
  );
}

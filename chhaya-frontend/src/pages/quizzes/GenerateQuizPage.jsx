import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { SelectField, TextField } from "../../components/ui/Field";
import { listCourses, listChapters } from "../../api/courses";
import { generateQuiz } from "../../api/quizzes";


export default function GenerateQuizPage() {
  const navigate = useNavigate();

  // Courses and chapters for the dropdowns
  const [courses, setCourses] = useState([]);
  const [chapters, setChapters] = useState([]);

  // Form state
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [selectedChapterId, setSelectedChapterId] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [marksPerQuestion, setMarksPerQuestion] = useState(2);
  const [difficulty, setDifficulty] = useState("medium");

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load courses on mount
  useEffect(() => {
    listCourses()
      .then(setCourses)
      .catch(() => setError("Could not load courses."));
  }, []);

  // Load chapters whenever the selected course changes
  async function handleCourseChange(courseId) {
    setSelectedCourseId(courseId);
    setSelectedChapterId("");
    setChapters([]);
    if (!courseId) return;
    try {
      const data = await listChapters(courseId);
      setChapters(data);
    } catch {
      setError("Could not load chapters for this course.");
    }
  }

  async function handleGenerate() {
    setError("");

    // Basic validation
    if (!selectedChapterId) {
      setError("Please select a chapter first.");
      return;
    }
    if (numQuestions < 1 || numQuestions > 20) {
      setError("Number of questions must be between 1 and 20.");
      return;
    }
    if (marksPerQuestion < 1 || marksPerQuestion > 10) {
      setError("Marks per question must be between 1 and 10.");
      return;
    }

    setLoading(true);
    try {
      const quiz = await generateQuiz(
        selectedChapterId,
        Number(numQuestions),
        Number(marksPerQuestion),
        difficulty
      );
      // Navigate straight to the quiz session page
      navigate(`/quizzes/${quiz.id}`);
    } catch (err) {
      // Show the backend's error message if available
      const detail = err.response?.data?.detail;
      setError(detail || "Could not generate quiz. Try adding more notes to the chapter.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell section="Learning" current="Quizzes">
      <div className="page-head">
        <div>
          <div className="page-title">Generate quiz</div>
          <div className="page-sub">Pick a chapter, configure the quiz, and let Gemini build it from your notes.</div>
        </div>
      </div>

      <div className="card card-pad" style={{ maxWidth: 520 }}>
        {error && <div className="banner banner-danger" style={{ marginBottom: 16 }}>{error}</div>}

        {/* Step 1: pick course */}
        <SelectField
          label="Course"
          value={selectedCourseId}
          onChange={(e) => handleCourseChange(e.target.value)}
        >
          <option value="">— select a course —</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>{c.title}</option>
          ))}
        </SelectField>

        {/* Step 2: pick chapter (only shown after a course is selected) */}
        {selectedCourseId && (
          <div style={{ marginTop: 16 }}>
            <SelectField
              label="Chapter (topic)"
              value={selectedChapterId}
              onChange={(e) => setSelectedChapterId(e.target.value)}
            >
              <option value="">— select a chapter —</option>
              {chapters.map((ch) => (
                <option key={ch.id} value={ch.id}>{ch.title}</option>
              ))}
            </SelectField>
          </div>
        )}

        {/* Step 3: quiz settings */}
        <div style={{ marginTop: 16 }}>
          <TextField
            label="Number of questions (1–20)"
            type="number"
            min={1}
            max={20}
            value={numQuestions}
            onChange={(e) => setNumQuestions(e.target.value)}
          />
        </div>

        <div style={{ marginTop: 16 }}>
          <TextField
            label="Marks per question (1–10)"
            type="number"
            min={1}
            max={10}
            value={marksPerQuestion}
            onChange={(e) => setMarksPerQuestion(e.target.value)}
          />
        </div>

        <div style={{ marginTop: 16 }}>
          <SelectField
            label="Difficulty"
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
          >
            <option value="easy">Easy (2 min / question)</option>
            <option value="medium">Medium (3 min / question)</option>
            <option value="hard">Hard (5 min / question)</option>
          </SelectField>
        </div>

        {/* Estimated duration hint */}
        {numQuestions > 0 && (
          <div className="hint" style={{ marginTop: 12 }}>
            Estimated duration: {numQuestions * (difficulty === "easy" ? 2 : difficulty === "hard" ? 5 : 3)} minutes
          </div>
        )}

        <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
          <Button
            variant="primary"
            disabled={loading || !selectedChapterId}
            onClick={handleGenerate}
          >
            {loading ? "Generating…" : "Generate quiz"}
          </Button>
          <Button variant="ghost" onClick={() => navigate("/quizzes")}>
            Cancel
          </Button>
        </div>
      </div>
    </AppShell>
  );
}

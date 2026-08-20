import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import { SelectField, TextField } from "../../components/ui/Field";
import { listCourses, listChapters } from "../../api/courses";
import { listNotes } from "../../api/notes";
import { generateQuiz } from "../../api/quizzes";


export default function GenerateQuizPage() {
  const navigate = useNavigate();

  // Cascading dropdown data
  const [courses, setCourses] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [notes, setNotes] = useState([]);

  // Selections
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [selectedChapterId, setSelectedChapterId] = useState("");
  const [selectedNoteId, setSelectedNoteId] = useState("");

  // Quiz settings
  const [numQuestions, setNumQuestions] = useState(5);
  const [minMarks, setMinMarks] = useState(2);
  const [maxMarks, setMaxMarks] = useState(5);
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

  // Load chapters when course changes
  async function handleCourseChange(courseId) {
    setSelectedCourseId(courseId);
    setSelectedChapterId("");
    setSelectedNoteId("");
    setChapters([]);
    setNotes([]);
    if (!courseId) return;
    try {
      const data = await listChapters(courseId);
      setChapters(data);
    } catch {
      setError("Could not load chapters for this course.");
    }
  }

  // Load notes when chapter changes
  async function handleChapterChange(chapterId) {
    setSelectedChapterId(chapterId);
    setSelectedNoteId("");
    setNotes([]);
    if (!chapterId) return;
    try {
      const data = await listNotes(chapterId);
      setNotes(data);
    } catch {
      setError("Could not load notes for this chapter.");
    }
  }

  async function handleGenerate() {
    setError("");

    // Client-side validation
    if (!selectedNoteId) {
      setError("Please select a note first.");
      return;
    }
    if (numQuestions < 1 || numQuestions > 20) {
      setError("Number of questions must be between 1 and 20.");
      return;
    }
    if (minMarks < 1 || minMarks > 10) {
      setError("Minimum marks must be between 1 and 10.");
      return;
    }
    if (Number(maxMarks) < Number(minMarks)) {
      setError("Maximum marks must be greater than or equal to minimum marks.");
      return;
    }
    if (maxMarks > 10) {
      setError("Maximum marks cannot exceed 10.");
      return;
    }

    setLoading(true);
    try {
      const quiz = await generateQuiz(
        selectedNoteId,
        Number(numQuestions),
        Number(minMarks),
        Number(maxMarks),
        difficulty
      );
      navigate(`/quizzes/${quiz.id}`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || "Could not generate quiz. Try adding more content to the note.");
    } finally {
      setLoading(false);
    }
  }

  // Label helper for note type badge
  function noteTypeLabel(note) {
    if (note.note_type === "text") return "Text";
    if (note.note_type === "pdf") return "PDF";
    if (note.note_type === "image") return "Image";
    return note.note_type;
  }

  return (
    <AppShell section="Learning" current="Quizzes">
      <div className="page-head">
        <div>
          <div className="page-title">Generate quiz</div>
          <div className="page-sub">Pick a note, configure the quiz, and let Gemini build it.</div>
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

        {/* Step 2: pick chapter */}
        {selectedCourseId && (
          <div style={{ marginTop: 16 }}>
            <SelectField
              label="Chapter (topic)"
              value={selectedChapterId}
              onChange={(e) => handleChapterChange(e.target.value)}
            >
              <option value="">— select a chapter —</option>
              {chapters.map((ch) => (
                <option key={ch.id} value={ch.id}>{ch.title}</option>
              ))}
            </SelectField>
          </div>
        )}

        {/* Step 3: pick a specific note */}
        {selectedChapterId && (
          <div style={{ marginTop: 16 }}>
            <SelectField
              label="Note to quiz from"
              value={selectedNoteId}
              onChange={(e) => setSelectedNoteId(e.target.value)}
            >
              <option value="">— select a note —</option>
              {notes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.title} [{noteTypeLabel(n)}]
                </option>
              ))}
            </SelectField>
            {notes.length === 0 && (
              <div className="hint" style={{ marginTop: 6 }}>
                No notes in this chapter yet. Add a note first.
              </div>
            )}
          </div>
        )}

        {/* Step 4: quiz settings (shown once a note is picked) */}
        {selectedNoteId && (
          <>
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

            {/* Marks range — two inputs side by side */}
            <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
              <div style={{ flex: 1 }}>
                <TextField
                  label="Minimum marks (1–10)"
                  type="number"
                  min={1}
                  max={10}
                  value={minMarks}
                  onChange={(e) => setMinMarks(e.target.value)}
                />
              </div>
              <div style={{ flex: 1 }}>
                <TextField
                  label="Maximum marks (≥ min)"
                  type="number"
                  min={1}
                  max={10}
                  value={maxMarks}
                  onChange={(e) => setMaxMarks(e.target.value)}
                />
              </div>
            </div>
            <div className="hint" style={{ marginTop: 6 }}>
              Gemini will assign each question a different marks value within this range based on complexity.
            </div>

            <div style={{ marginTop: 16 }}>
              <SelectField
                label="Difficulty"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="easy">Easy (base 2 min / question)</option>
                <option value="medium">Medium (base 3 min / question)</option>
                <option value="hard">Hard (base 5 min / question)</option>
              </SelectField>
            </div>

            {/* Estimated duration hint */}
            {numQuestions > 0 && minMarks > 0 && Number(maxMarks) >= Number(minMarks) && (
              <div className="hint" style={{ marginTop: 12 }}>
                Estimated duration: ~{Math.ceil(
                  numQuestions * ((difficulty === "easy" ? 2 : difficulty === "hard" ? 5 : 3) +
                  ((Number(minMarks) + Number(maxMarks)) / 2) * 0.5)
                )} minutes
              </div>
            )}
          </>
        )}

        <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
          <Button
            variant="primary"
            disabled={loading || !selectedNoteId}
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

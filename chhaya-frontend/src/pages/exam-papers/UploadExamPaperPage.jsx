import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { TextField } from "../../components/ui/Field";
import { uploadExamPaper } from "../../api/examPapers";

export default function UploadExamPaperPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [course, setCourse] = useState("");
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setError("Choose an image or PDF file to upload.");
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      const paper = await uploadExamPaper({ title, course, file });
      navigate(`/exam-papers/${paper.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not upload that file.");
      setSubmitting(false);
    }
  }

  return (
    <AppShell section="Upload questions" current="Upload paper">
      <div className="page-head">
        <div>
          <div className="page-title">Upload a past exam paper</div>
          <div className="page-sub">A photo or scan works — Chhaya reads the text with OCR.</div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: 520 }}>
        <div className="form-grid">
          <TextField label="Title" placeholder="Midterm 2024" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <TextField label="Course (optional)" placeholder="CSE220" value={course} onChange={(e) => setCourse(e.target.value)} />
          <div className="field">
            <div className="label">File</div>
            <div className="upload-drop">
              <input
                type="file"
                accept="image/*,.pdf,application/pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                style={{ marginBottom: 8 }}
              />
              <div className="hint">JPG, PNG, or PDF files.</div>

            </div>
          </div>
        </div>
        <div className="form-foot">
          <Button type="submit" disabled={submitting} icon={<Icon name="fileText" size={16} />}>
            {submitting ? "Uploading..." : "Upload and extract text"}
          </Button>
          <Button type="button" variant="ghost" onClick={() => navigate("/exam-papers")}>Cancel</Button>
          {error && <div className="error-text" style={{ marginLeft: 8 }}>{error}</div>}
        </div>
      </form>
    </AppShell>
  );
}

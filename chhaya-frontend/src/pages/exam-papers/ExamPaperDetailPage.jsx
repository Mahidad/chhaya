import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { getExamPaper, deleteExamPaper } from "../../api/examPapers";

export default function ExamPaperDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [paper, setPaper] = useState(null);

  useEffect(() => {
    let cancelled = false;
    let timer;
    async function tick() {
      const data = await getExamPaper(id);
      if (cancelled) return;
      setPaper(data);
      if (data.status === "pending" || data.status === "processing") {
        timer = setTimeout(tick, 2000);
      }
    }
    tick();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [id]);

  async function handleDelete() {
    if (!window.confirm("Are you sure you want to delete this question paper?")) return;
    try {
      await deleteExamPaper(id);
      navigate("/exam-papers");
    } catch {
      alert("Could not delete question paper.");
    }
  }

  if (!paper) {
    return (
      <AppShell section="Upload questions" current="Loading">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  if (paper.status === "pending" || paper.status === "processing") {
    return (
      <AppShell section="Upload questions" current="Reading">
        <div className="page-head">
          <div>
            <div className="page-title">Reading {paper.title}</div>
            <div className="page-sub">Running OCR on the upload.</div>
          </div>
        </div>
        <div className="card card-pad">
          <div className="progress">
            <div className="progress-fill" style={{ width: "50%", animation: "chhaya-indeterminate 1.4s ease-in-out infinite" }} />
          </div>
        </div>
      </AppShell>
    );
  }

  if (paper.status === "failed") {
    return (
      <AppShell section="Upload questions" current="Could not read paper">
        <div className="page-head">
          <div>
            <div className="page-title">This paper could not be read</div>
            <div className="page-sub">{paper.title}</div>
          </div>
          <div className="page-actions">
            <Button variant="ghost" onClick={handleDelete} icon={<Icon name="trash" size={16} />}>Delete</Button>
            <Button variant="ghost" onClick={() => navigate("/exam-papers")}>Back</Button>
          </div>
        </div>
        <div className="banner banner-danger">
          <Icon name="alertTriangle" size={20} />
          <div>
            <div className="banner-title">OCR failed</div>
            <div className="banner-copy">{paper.error_message}</div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Upload questions" current={paper.title}>
      <div className="page-head">
        <div>
          <div className="page-title">{paper.title}</div>
          <div className="page-sub">{paper.course}</div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" onClick={handleDelete} icon={<Icon name="trash" size={16} />}>Delete</Button>
          <Button variant="ghost" onClick={() => navigate("/exam-papers")}>Back</Button>
        </div>
      </div>
      <div className="card">
        <div className="card-head"><span className="card-title">Extracted text</span></div>
        <div className="guide-body">{paper.extracted_text}</div>
      </div>
    </AppShell>
  );
}


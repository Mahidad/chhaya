import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { listExamPapers, deleteExamPaper } from "../../api/examPapers";

const STATUS_BADGE = {
  pending: { variant: undefined, label: "Pending" },
  processing: { variant: "amber", label: "Reading" },
  ready: { variant: "ok", label: "Ready" },
  failed: { variant: "danger", label: "Failed" },
};

export default function ExamPapersListPage() {
  const [papers, setPapers] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    listExamPapers().then(setPapers).catch(() => setPapers([]));
  }, []);

  async function handleDelete(e, id) {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this question paper?")) return;
    try {
      await deleteExamPaper(id);
      setPapers((prev) => prev.filter((p) => p.id !== id));
    } catch {
      alert("Could not delete question paper.");
    }
  }

  if (papers === null) {
    return (
      <AppShell section="Upload questions" current="Uploaded questions">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Upload questions" current="Uploaded questions">
      <div className="page-head">
        <div>
          <div className="page-title">Uploaded question papers</div>
          <div className="page-sub">Upload a scanned paper — Chhaya reads it and keeps the format as a reference.</div>
        </div>
        <div className="page-actions">
          <Button icon={<Icon name="plus" size={16} />} onClick={() => navigate("/exam-papers/new")}>
            Upload a paper
          </Button>
        </div>
      </div>

      {papers.length === 0 ? (
        <div className="ingest-empty">
          <div className="shadow-mark">
            <div className="disc disc-back" />
            <div className="disc disc-front"><Icon name="exams" size={22} /></div>
          </div>
          <div className="empty-title">No question papers yet</div>
          <div className="empty-copy">Upload a scanned exam paper — a photo, screenshot, or PDF works.</div>
          <div className="empty-actions">
            <Button size="lg" icon={<Icon name="plus" size={16} />} onClick={() => navigate("/exam-papers/new")}>
              Upload your first paper
            </Button>
          </div>
        </div>
      ) : (
        <div className="list-card">
          {papers.map((p) => {
            const status = STATUS_BADGE[p.status] || STATUS_BADGE.pending;
            return (
              <div key={p.id} style={{ display: "flex", alignItems: "center" }}>
                <Link to={`/exam-papers/${p.id}`} className="prow" style={{ flex: 1, textDecoration: "none", color: "inherit" }}>
                  <div className="avatar av-ink"><Icon name="exams" size={15} /></div>
                  <div className="prow-id" style={{ flex: 1 }}>
                    <div className="prow-name">{p.title}</div>
                    {p.course && <div className="prow-course">{p.course}</div>}
                  </div>
                  <Badge variant={status.variant}>{status.label}</Badge>
                </Link>
                <button
                  type="button"
                  title="Delete question paper"
                  onClick={(e) => handleDelete(e, p.id)}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: "8px 12px",
                    color: "var(--muted, #888)",
                  }}
                >
                  <Icon name="trash" size={16} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}


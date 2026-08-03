import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { getExamPaper, deleteExamPaper, getExamPaperFileBlob } from "../../api/examPapers";

export default function ExamPaperDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [paper, setPaper] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [fileType, setFileType] = useState("");
  const [activeTab, setActiveTab] = useState("split"); // 'split', 'text', 'file'

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

  useEffect(() => {
    let url = null;
    if (paper && (paper.status === "ready" || paper.status === "failed")) {
      getExamPaperFileBlob(id)
        .then((blob) => {
          url = URL.createObjectURL(blob);
          setFileUrl(url);
          setFileType(blob.type);
        })
        .catch(() => {});
    }
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [id, paper]);

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

  const isPdf = fileType.includes("pdf") || (paper.file_path && paper.file_path.toLowerCase().endsWith(".pdf"));

  return (
    <AppShell section="Upload questions" current={paper.title}>
      <div className="page-head">
        <div>
          <div className="page-title">{paper.title}</div>
          <div className="page-sub">{paper.course}</div>
        </div>
        <div className="page-actions" style={{ display: "flex", gap: 8 }}>
          <div className="btn-group" style={{ display: "flex", gap: 4, background: "var(--surface-subtle, #f5f5f5)", padding: 4, borderRadius: 6 }}>
            <Button
              variant={activeTab === "split" ? "primary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("split")}
            >
              Side-by-side
            </Button>
            <Button
              variant={activeTab === "file" ? "primary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("file")}
            >
              Uploaded Document
            </Button>
            <Button
              variant={activeTab === "text" ? "primary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("text")}
            >
              Extracted Text
            </Button>
          </div>
          <Button variant="ghost" onClick={handleDelete} icon={<Icon name="trash" size={16} />}>Delete</Button>
          <Button variant="ghost" onClick={() => navigate("/exam-papers")}>Back</Button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: activeTab === "split" ? "1fr 1fr" : "1fr", gap: 16 }}>
        {(activeTab === "split" || activeTab === "file") && (
          <div className="card" style={{ display: "flex", flexDirection: "column", height: 600 }}>
            <div className="card-head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="card-title">Uploaded Document ({isPdf ? "PDF" : "Image"})</span>
              {fileUrl && (
                <a href={fileUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: 13, textDecoration: "none", color: "var(--primary)" }}>
                  Open full size ↗
                </a>
              )}
            </div>
            <div style={{ flex: 1, padding: 12, overflow: "auto", display: "flex", justifyContent: "center", alignItems: "center", background: "#f8f9fa" }}>
              {fileUrl ? (
                isPdf ? (
                  <iframe src={fileUrl} title="Uploaded PDF" style={{ width: "100%", height: "100%", border: "none", borderRadius: 4 }} />
                ) : (
                  <img src={fileUrl} alt={paper.title} style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", borderRadius: 4 }} />
                )
              ) : (
                <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading document viewer...</div>
              )}
            </div>
          </div>
        )}

        {(activeTab === "split" || activeTab === "text") && (
          <div className="card" style={{ display: "flex", flexDirection: "column", height: 600 }}>
            <div className="card-head"><span className="card-title">Extracted Text (OCR)</span></div>
            <div className="guide-body" style={{ flex: 1, overflowY: "auto", whiteSpace: "pre-wrap", padding: 16 }}>
              {paper.extracted_text || "No text extracted."}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}



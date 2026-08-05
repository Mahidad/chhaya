import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import Markdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { getStudyGuide, deleteStudyGuide, renameStudyGuide } from "../../api/studyGuides";
import { recordGuideView } from "../../api/progress";

export default function GuideDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [guide, setGuide] = useState(null);
  const [viewLang, setViewLang] = useState("en");

  useEffect(() => {
    let cancelled = false;
    let timer;
    async function tick() {
      const data = await getStudyGuide(id);
      if (cancelled) return;
      setGuide(data);
      if (data.status === "pending" || data.status === "generating") {
        timer = setTimeout(tick, 2000);
      }
    }
    tick();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [id]);

  useEffect(() => {
    if (guide && guide.status === "done") {
      recordGuideView(id).catch(() => {});
    }
  }, [guide?.status, id]);

  async function handleDelete() {
    if (window.confirm("Are you sure you want to delete this study guide?")) {
      await deleteStudyGuide(id);
      navigate("/guides");
    }
  }

  async function handleRename() {
    const newTopic = window.prompt("Enter new topic for study guide:", guide?.topic);
    if (newTopic && newTopic.trim() !== "") {
      const updated = await renameStudyGuide(id, newTopic.trim());
      setGuide(updated);
    }
  }

  if (!guide) {
    return (
      <AppShell section="Study guides" current="Loading">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  if (guide.status === "pending" || guide.status === "generating") {
    return (
      <AppShell section="Study guides" current="Generating">
        <div className="page-head">
          <div>
            <div className="page-title">Writing "{guide.topic}"</div>
            <div className="page-sub">Usually takes under a minute.</div>
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

  if (guide.status === "failed") {
    return (
      <AppShell section="Study guides" current="Could not generate">
        <div className="page-head">
          <div>
            <div className="page-title">This guide could not be generated</div>
            <div className="page-sub">{guide.topic}</div>
          </div>
          <div className="page-actions">
            <Button variant="ghost" onClick={() => navigate("/guides")}>Back to guides</Button>
          </div>
        </div>
        <div className="banner banner-danger">
          <Icon name="alertTriangle" size={20} />
          <div>
            <div className="banner-title">Generation failed</div>
            <div className="banner-copy">{guide.error_message || "An unknown error interrupted generation."}</div>
          </div>
        </div>
      </AppShell>
    );
  }

  const activeContent = (viewLang === "bn" && guide.bangla_content) ? guide.bangla_content : guide.content;

  return (
    <AppShell section="Study guides" current={guide.topic}>
      <div className="page-head">
        <div>
          <div className="page-title">{guide.topic}</div>
          <div className="page-sub">{guide.depth} depth</div>
        </div>
        <div className="page-actions">
          {guide.bangla_content && (
            <div className="lang-toggle" style={{ marginRight: 8 }}>
              <button
                className={`lang-option ${viewLang === "en" ? "active" : ""}`}
                onClick={() => setViewLang("en")}
              >
                EN
              </button>
              <button
                className={`lang-option bn ${viewLang === "bn" ? "active" : ""}`}
                onClick={() => setViewLang("bn")}
              >
                বাংলা
              </button>
            </div>
          )}
          <Button variant="ghost" onClick={handleRename}>Rename</Button>
          <Button variant="danger" onClick={handleDelete}>Delete</Button>
        </div>
      </div>

      <div className="split">
        <div className="col-form card">
          <div className="card-head">
            <span className="card-title">
              {viewLang === "bn" ? "স্টাডি গাইড (বাংলা)" : "Guide"}
            </span>
          </div>
          <div className="guide-body">
            <Markdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
              {activeContent}
            </Markdown>
          </div>
        </div>
        <div className="col-side">
          {guide.formula_sheet_content && (
            <div className="card">
              <div className="card-head"><span className="card-title">Formula sheet</span></div>
              <div className="guide-body">
                <Markdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                  {guide.formula_sheet_content}
                </Markdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import Markdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import rehypeTextify from "../../utils/rehypeTextify";
import { getStudyGuide, deleteStudyGuide, renameStudyGuide, updateStudyGuideContent } from "../../api/studyGuides";
import { recordGuideView } from "../../api/progress";
import AnnotatableText, { HighlightableText } from "../../components/annotations/AnnotatableText";
import { ContentType } from "../../constants/contentTypes";
import VoiceNarrationPlayer from "../../components/voice/VoiceNarrationPlayer";

export default function GuideDetailPage() {
  const { id, courseId, chapterId, guideId } = useParams();
  const actualId = guideId || id;
  const navigate = useNavigate();
  const [guide, setGuide] = useState(null);
  const [viewLang, setViewLang] = useState("en");

  const isCoursesContext = !!(courseId && chapterId);
  const isReadOnly = false; // Enable editing tools (highlight, sticky note, define, edit text & formulas) everywhere
  const effectiveChapterId = chapterId || guide?.chapter_id || "unfiled";

  const [editingContent, setEditingContent] = useState(false);
  const [contentDraft, setContentDraft] = useState("");
  const [editingFormula, setEditingFormula] = useState(false);
  const [formulaDraft, setFormulaDraft] = useState("");

  useEffect(() => {
    let cancelled = false;
    let timer;
    async function tick() {
      const data = await getStudyGuide(actualId);
      if (cancelled) return;
      setGuide(data);
      if (data.status === "pending" || data.status === "generating") {
        timer = setTimeout(tick, 2000);
      }
    }
    tick();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [actualId]);

  useEffect(() => {
    // NOTE: the backend (app/models/study_guide.py's GuideStatus) only
    // ever sets "ready", never "done" -- keep this in sync if it drifts
    // again, since view-tracking silently stops firing otherwise.
    if (guide && guide.status === "ready") {
      recordGuideView(actualId).catch(() => {});
    }
  }, [guide?.status, actualId]);

  async function handleDelete() {
    if (window.confirm("Are you sure you want to delete this study guide?")) {
      await deleteStudyGuide(actualId);
      if (isCoursesContext) {
        navigate(`/courses/${courseId}/chapters/${chapterId}`);
      } else {
        navigate("/guides");
      }
    }
  }

  async function handleRename() {
    const newTopic = window.prompt("Enter new topic for study guide:", guide?.topic);
    if (newTopic && newTopic.trim() !== "") {
      const updated = await renameStudyGuide(actualId, newTopic.trim());
      setGuide(updated);
    }
  }

  async function handleSaveContent() {
    const updated = await updateStudyGuideContent(actualId, { content: contentDraft });
    setGuide(updated);
    setEditingContent(false);
  }

  async function handleSaveFormula() {
    const updated = await updateStudyGuideContent(actualId, { formulaSheetContent: formulaDraft });
    setGuide(updated);
    setEditingFormula(false);
  }

  function handleExportPDF() {
    window.print();
  }

  if (!guide) {
    return (
      <AppShell section={isCoursesContext ? "Courses" : "Study guides"} current="Loading">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  if (guide.status === "pending" || guide.status === "generating") {
    return (
      <AppShell section={isCoursesContext ? "Courses" : "Study guides"} current="Generating">
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
      <AppShell section={isCoursesContext ? "Courses" : "Study guides"} current="Could not generate">
        <div className="page-head">
          <div>
            <div className="page-title">This guide could not be generated</div>
            <div className="page-sub">{guide.topic}</div>
          </div>
          <div className="page-actions">
            <Button variant="ghost" onClick={() => isCoursesContext ? navigate(`/courses/${courseId}/chapters/${chapterId}`) : navigate("/guides")}>
              Back
            </Button>
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
    <AppShell section={isCoursesContext ? "Courses" : "Study guides"} current={guide.topic}>
      <div className="page-head">
        <div>
          {isCoursesContext && (
            <Link to={`/courses/${courseId}/chapters/${chapterId}`} className="hint" style={{ marginBottom: 4, display: "inline-block" }}>
              &larr; Back to chapter
            </Link>
          )}
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
          <Button variant="ghost" icon={<Icon name="fileText" size={16} />} onClick={handleExportPDF}>
            Export to PDF
          </Button>
          <Button variant="ghost" onClick={handleRename}>Rename</Button>
          <Button variant="danger" onClick={handleDelete}>Delete</Button>
        </div>
      </div>

      <div className="split">
        <div className="col-form card">
          <div className="card-head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="card-title">
              {viewLang === "bn" ? "স্টাডি গাইড (বাংলা)" : "Guide"}
            </span>
            {!editingContent && (
              <button
                className="mini-btn"
                onClick={() => { setEditingContent(true); setContentDraft(activeContent || ""); }}
                style={{ fontSize: 12, cursor: "pointer" }}
              >
                Edit text & formulas
              </button>
            )}
          </div>
          <div className="guide-body">
            {editingContent ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div className="hint" style={{ fontSize: 11 }}>
                  Add text, lines, or LaTeX math formulas (e.g. <code>$E=mc^2$</code> or <code>$$\frac&#123;a&#125;&#123;b&#125;$$</code>). Live KaTeX preview updates below as you type.
                </div>
                <textarea
                  value={contentDraft}
                  onChange={(e) => setContentDraft(e.target.value)}
                  style={{ width: "100%", minHeight: 220, fontFamily: "monospace", fontSize: 13, padding: 8, borderRadius: 6, border: "1px solid var(--border)" }}
                />
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--primary-dark)" }}>Live Preview:</div>
                <div style={{ padding: 12, border: "1px dashed var(--border)", borderRadius: 6, backgroundColor: "var(--bg-card)" }}>
                  <Markdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                    {contentDraft}
                  </Markdown>
                </div>
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                  <Button size="sm" onClick={handleSaveContent}>Save edits</Button>
                  <Button size="sm" variant="ghost" onClick={() => setEditingContent(false)}>Cancel</Button>
                </div>
              </div>
            ) : (
              <AnnotatableText 
                chapterId={effectiveChapterId} 
                contentType={ContentType.STUDY_GUIDE} 
                contentId={guide.id}
                topic={guide.topic}
                readOnly={false}
              >
                <Markdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex, rehypeTextify]}
                  components={{ htext: HighlightableText }}
                >
                  {activeContent}
                </Markdown>
              </AnnotatableText>
            )}
          </div>
        </div>
        <div className="col-side">
          {guide.formula_sheet_content && (
            <div className="card">
              <div className="card-head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="card-title">Formula sheet</span>
                {!editingFormula && (
                  <button
                    className="mini-btn"
                    onClick={() => { setEditingFormula(true); setFormulaDraft(guide.formula_sheet_content || ""); }}
                    style={{ fontSize: 12, cursor: "pointer" }}
                  >
                    Edit formulas
                  </button>
                )}
              </div>
              <div className="guide-body">
                {editingFormula ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <textarea
                      value={formulaDraft}
                      onChange={(e) => setFormulaDraft(e.target.value)}
                      style={{ width: "100%", minHeight: 160, fontFamily: "monospace", fontSize: 13, padding: 8, borderRadius: 6, border: "1px solid var(--border)" }}
                    />
                    <div style={{ fontSize: 12, fontWeight: 600, color: "var(--primary-dark)" }}>Live KaTeX Preview:</div>
                    <div style={{ padding: 12, border: "1px dashed var(--border)", borderRadius: 6, backgroundColor: "var(--bg-card)" }}>
                      <Markdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                        {formulaDraft}
                      </Markdown>
                    </div>
                    <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                      <Button size="sm" onClick={handleSaveFormula}>Save formulas</Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingFormula(false)}>Cancel</Button>
                    </div>
                  </div>
                ) : (
                  <AnnotatableText 
                    chapterId={effectiveChapterId} 
                    contentType={ContentType.STUDY_GUIDE} 
                    contentId={`${guide.id}-formula`}
                    topic={guide.topic + " Formulas"}
                    readOnly={false}
                  >
                    <Markdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex, rehypeTextify]}
                      components={{ htext: HighlightableText }}
                    >
                      {guide.formula_sheet_content}
                    </Markdown>
                  </AnnotatableText>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <VoiceNarrationPlayer studyGuideId={guide.id} />
    </AppShell>
  );
}


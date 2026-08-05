import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { getStudyGuide } from "../../api/studyGuides";
import { recordGuideView } from "../../api/progress"; // Module 1 Feature 4 – analytics

export default function GuideDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [guide, setGuide] = useState(null);

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

  // Record a guide-view event for analytics once the guide finishes loading.
  // Fire-and-forget: errors are swallowed so a tracking failure never
  // disrupts the actual guide view (Amiyo's Module 1 Feature 4).
  useEffect(() => {
    if (guide && guide.status === "done") {
      recordGuideView(id).catch(() => {});
    }
  }, [guide?.status, id]);

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

  return (
    <AppShell section="Study guides" current={guide.topic}>
      <div className="page-head">
        <div>
          <div className="page-title">{guide.topic}</div>
          <div className="page-sub">{guide.depth} depth</div>
        </div>
      </div>

      <div className="split">
        <div className="col-form card">
          <div className="card-head"><span className="card-title">Guide</span></div>
          <div className="guide-body">{guide.content}</div>
        </div>
        <div className="col-side">
          {guide.formula_sheet_content && (
            <div className="card">
              <div className="card-head"><span className="card-title">Formula sheet</span></div>
              <div className="guide-body">{guide.formula_sheet_content}</div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

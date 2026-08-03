import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { listStudyGuides } from "../../api/studyGuides";

/*
  Simplified vs. lamia-f1-01-empty.html: the mockup's empty state has a
  decorative "paper mock" illustration and a row of suggested-topic chips
  pulled from the student's enrolled courses (a concept that doesn't exist
  in the data model yet). Reused the same `.ingest-empty` block Reference
  Sources uses instead of building a second bespoke empty-state look --
  worth a real design pass once course enrollment is modeled.
*/
const STATUS_BADGE = {
  pending: { variant: undefined, label: "Pending" },
  generating: { variant: "amber", label: "Generating" },
  ready: { variant: "ok", label: "Ready" },
  failed: { variant: "danger", label: "Failed" },
};

export default function StudyGuidesListPage() {
  const [guides, setGuides] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    listStudyGuides().then(setGuides).catch(() => setGuides([]));
  }, []);

  if (guides === null) {
    return (
      <AppShell section="Study guides" current="All guides">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Study guides" current="All guides">
      <div className="page-head">
        <div>
          <div className="page-title">Study guides</div>
          <div className="page-sub">
            Pick a topic, pick a teacher's style, and Chhaya writes the chapter — even one your teacher never uploaded.
          </div>
        </div>
        {guides.length > 0 && (
          <div className="page-actions">
            <Button icon={<Icon name="plus" size={16} />} onClick={() => navigate("/guides/new")}>
              New study guide
            </Button>
          </div>
        )}
      </div>

      {guides.length === 0 ? (
        <div className="ingest-empty">
          <div className="shadow-mark">
            <div className="disc disc-back" />
            <div className="disc disc-front"><Icon name="guides" size={22} /></div>
          </div>
          <div className="empty-title">No study guides yet</div>
          <div className="empty-copy">
            A guide is a full written chapter in a teacher's style, with a formula sheet if the topic is STEM.
          </div>
          <div className="empty-actions">
            <Button size="lg" icon={<Icon name="plus" size={16} />} onClick={() => navigate("/guides/new")}>
              Write my first guide
            </Button>
            <Link to="/library" className="btn btn-ghost btn-lg">
              <Icon name="library" size={16} /> Browse style library
            </Link>
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {guides.map((g) => {
            const status = STATUS_BADGE[g.status] || STATUS_BADGE.pending;
            return (
              <Link key={g.id} to={`/guides/${g.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <div className="card card-pad">
                  <div className="thumb"><Icon name="guides" size={26} /></div>
                  <div className="src-title">{g.topic}</div>
                  <div className="src-meta">
                    <Badge variant={status.variant}>{status.label}</Badge>
                    <span>{g.depth}</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}

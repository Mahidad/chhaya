import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import Icon from "../../components/icons/Icon";
import { listReferenceSources } from "../../api/referenceSources";

/*
  This page covers TWO Figma states (mahidad-f1-01-empty.html for zero
  sources) plus a populated grid the mockups didn't include a screen for
  (the export only showed the empty state for the list view). The card
  design below reuses the same `.thumb` / `.src-title` / badge classes
  from the detail screens so it doesn't feel invented -- it borrows the
  vocabulary that already exists elsewhere in the mockup.
*/

const STATUS_BADGE = {
  pending: { variant: undefined, label: "Pending" },
  processing: { variant: "amber", label: "Analysing" },
  ready: { variant: "ok", label: "Ready" },
  failed: { variant: "danger", label: "Needs attention" },
};

export default function ReferenceSourcesListPage() {
  const [sources, setSources] = useState(null); // null = loading
  const navigate = useNavigate();

  useEffect(() => {
    listReferenceSources().then(setSources).catch(() => setSources([]));
  }, []);

  if (sources === null) {
    return (
      <AppShell section="Reference sources" current="All sources">
        <div className="page-head">
          <div>
            <div className="page-title">Reference sources</div>
          </div>
        </div>
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell section="Reference sources" current="All sources">
      <div className="page-head">
        <div>
          <div className="page-title">Reference sources</div>
          <div className="page-sub">
            Point Chhaya at a teacher you already learn from. It reads their lectures and keeps the style.
          </div>
        </div>
        {sources.length > 0 && (
          <div className="page-actions">
            <Button variant="primary" icon={<Icon name="plus" size={16} />} onClick={() => navigate("/sources/new")}>
              Add reference source
            </Button>
          </div>
        )}
      </div>

      {sources.length === 0 ? (
        <>
          <div className="ingest-empty">
            <div className="shadow-mark">
              <div className="disc disc-back" />
              <div className="disc disc-front">
                <Icon name="sources" size={22} strokeWidth="2" />
              </div>
            </div>
            <div className="empty-title">No reference sources yet</div>
            <div className="empty-copy">
              Paste a YouTube playlist or a course link from a teacher whose explanations already work for you.
              Chhaya pulls the transcripts and turns them into a reusable teaching-style profile.
            </div>
            <div className="empty-actions">
              <Button variant="primary" size="lg" icon={<Icon name="plus" size={16} />} onClick={() => navigate("/sources/new")}>
                Add your first source
              </Button>
              <Button variant="ghost" size="lg">See how style profiles work</Button>
            </div>
          </div>

          <div className="pipeline-row">
            <div className="pipe-card">
              <div className="pipe-num">STEP 1</div>
              <div className="pipe-title">Transcript is pulled and cleaned</div>
              <div className="pipe-copy">Captions come in, filler words and timestamps go out.</div>
              <div className="pipe-api">youtube-transcript-api</div>
            </div>
            <div className="pipe-card">
              <div className="pipe-num">STEP 2</div>
              <div className="pipe-title">Teaching style is analysed</div>
              <div className="pipe-copy">Pacing, vocabulary, analogies, example density, sequencing.</div>
              <div className="pipe-api">Gemini</div>
            </div>
            <div className="pipe-card">
              <div className="pipe-num">STEP 3</div>
              <div className="pipe-title">Profile is stored and reused</div>
              <div className="pipe-copy">Every guide, quiz and concept map can borrow this voice.</div>
              <div className="pipe-api">Style library</div>
            </div>
          </div>
        </>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {sources.map((source) => {
            const status = STATUS_BADGE[source.status] || STATUS_BADGE.pending;
            return (
              <Link key={source.id} to={`/sources/${source.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <Card className="card-pad" style={{ height: "100%" }}>
                  <div className="thumb">
                    <Icon name="sources" size={26} strokeWidth="1.6" />
                  </div>
                  <div className="src-title">{source.title}</div>
                  <div className="src-meta">
                    <Badge variant={status.variant}>{status.label}</Badge>
                    <span>{source.videos.length} video{source.videos.length === 1 ? "" : "s"}</span>
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}

import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import AnalysingPanel from "../../components/reference-sources/AnalysingPanel";
import { getReferenceSource, getSourceProfiles } from "../../api/referenceSources";

// Categorical backend values -> an approximate meter fill. The backend
// reports levels ("slow"/"moderate"/"fast"), not fabricated decimal
// scores -- we're not going to invent false precision the model didn't
// actually produce.
const LEVEL_TO_PERCENT = {
  low: 30, slow: 30, beginner: 30,
  medium: 60, moderate: 60, intermediate: 60,
  high: 88, fast: 88, advanced: 88,
};
const percentFor = (level) => LEVEL_TO_PERCENT[level?.toLowerCase()] ?? 50;

export default function SourceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [source, setSource] = useState(null);
  const [profiles, setProfiles] = useState(null); // array now -- a playlist can produce more than one
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [profileError, setProfileError] = useState(false);

  async function handleDelete() {
    if (window.confirm("Are you sure you want to remove this reference source?")) {
      await deleteReferenceSource(id);
      navigate("/sources");
    }
  }

  async function handleRename() {
    const newTitle = window.prompt("Enter new title for reference source:", source?.title);
    if (newTitle && newTitle.trim() !== "") {
      const updated = await renameReferenceSource(id, newTitle.trim());
      setSource(updated);
    }
  }

  const load = useCallback(async () => {
    const data = await getReferenceSource(id);
    setSource(data);
    if (data.status === "ready") {
      try {
        const list = await getSourceProfiles(id);
        setProfiles(list);
        setSelectedProfileId((current) => current || list[0]?.id || null);
      } catch {
        setProfileError(true);
      }
    }
    return data;
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    let timer;

    async function tick() {
      const data = await load();
      if (!cancelled && (data.status === "pending" || data.status === "processing")) {
        timer = setTimeout(tick, 2500);
      }
    }
    tick();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [load]);

  if (!source) {
    return (
      <AppShell section="Reference sources" current="Loading">
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
      </AppShell>
    );
  }

  if (source.status === "pending" || source.status === "processing") {
    return (
      <AppShell section="Reference sources" current="Analysing">
        <div className="page-head">
          <div>
            <div className="page-title">Reading {source.title}</div>
            <div className="page-sub">
              {source.source_type === "youtube_playlist"
                ? "Grouping videos by instructor and building a style profile per teacher."
                : "Keep this tab open, it runs in the background too."}
            </div>
          </div>
        </div>
        <AnalysingPanel title="Building the style profile" subtitle="This usually takes under a minute" />
      </AppShell>
    );
  }

  if (source.status === "failed") {
    return (
      <AppShell section="Reference sources" current="Could not read source">
        <div className="page-head">
          <div>
            <div className="page-title">This source could not be read</div>
            <div className="page-sub">{source.title}</div>
          </div>
          <div className="page-actions">
            <Button variant="ghost" icon={<Icon name="chevronRight" size={16} style={{ transform: "rotate(180deg)" }} />} onClick={() => navigate("/sources")}>
              Back to sources
            </Button>
          </div>
        </div>
        <div className="banner banner-danger">
          <Icon name="alertTriangle" size={20} />
          <div>
            <div className="banner-title">Transcript could not be fetched</div>
            <div className="banner-copy">{source.error_message || "An unknown error interrupted ingestion."}</div>
          </div>
          <div className="banner-actions">
            <Link to="/sources/new" className="btn btn-primary btn-sm">Try a different link</Link>
          </div>
        </div>
        <div className="hint">
          Common causes: the video's captions are turned off, the video is private/age-restricted, or the link
          wasn't a direct YouTube video URL.
        </div>
      </AppShell>
    );
  }

  // status === "ready"
  const profile = profiles?.find((p) => p.id === selectedProfileId) || null;
  const style = profile?.raw_style_profile || {};
  const hasMultipleProfiles = profiles?.length > 1;

  return (
    <AppShell section="Reference sources" current="Style profile">
      <div className="page-head">
        <div>
          <div className="page-title">Style profile ready</div>
          <div className="page-sub">
            {source.title}
            {profiles && ` · ${profiles.length} teaching style${profiles.length === 1 ? "" : "s"} detected`}
          </div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" onClick={handleRename}>Rename</Button>
          <Button variant="danger" onClick={handleDelete}>Delete</Button>
          <Button variant="primary" icon={<Icon name="check" size={16} strokeWidth="2.4" />} onClick={() => navigate("/library")}>
            Save to style library
          </Button>
        </div>
      </div>

      {hasMultipleProfiles && (
        <div className="banner">
          <Icon name="sources" size={20} />
          <div>
            <div className="banner-title">This playlist has more than one instructor</div>
            <div className="banner-copy">
              Chhaya grouped the videos by channel and built a separate style profile for each. Pick one below.
            </div>
          </div>
        </div>
      )}

      {hasMultipleProfiles && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
          {profiles.map((p) => (
            <button
              key={p.id}
              type="button"
              className={`chip ${p.id === selectedProfileId ? "chip-on" : ""}`}
              onClick={() => setSelectedProfileId(p.id)}
            >
              {p.channel_name || p.display_name}
              {p.match_score != null && (
                <span style={{ marginLeft: 6, opacity: 0.75 }}>· {Math.round(p.match_score)}%</span>
              )}
            </button>
          ))}
        </div>
      )}

      {profileError ? (
        <div className="hint">Profile details couldn't be loaded — try refreshing.</div>
      ) : !profile ? (
        <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading profile...</div>
      ) : (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="id-card">
              <div className="id-shadow">
                <div className="ghost" />
                <div className="avatar avatar-lg">{profile.display_name.slice(0, 2).toUpperCase()}</div>
              </div>
              <div>
                <div className="id-name">{profile.display_name}</div>
                <div className="id-meta">
                  {source.videos.filter((v) => v.teacher_profile_id === profile.id).length} video(s) from this instructor
                </div>
                <div className="id-tags">
                  {profile.match_score != null && (
                    <Badge variant={profile.match_score >= 75 ? "ok" : profile.match_score >= 50 ? "amber" : "danger"}>
                      {Math.round(profile.match_score)}% match with your preference
                    </Badge>
                  )}
                  {profile.analogy_frequency === "high" && <Badge variant="primary">Analogy-heavy</Badge>}
                  {profile.vocabulary_level && <Badge variant="iris">{profile.vocabulary_level} vocabulary</Badge>}
                  {style._mock && <Badge variant="amber">Mock profile — add GEMINI_API_KEY for real analysis</Badge>}
                </div>
              </div>
            </div>
          </div>

          <div className="split">
            <div className="col-form card">
              <div className="card-head">
                <span className="card-title">Style fingerprint</span>
                <span className="card-note">Four measured dimensions</span>
              </div>
              {[
                ["Pacing", profile.pacing],
                ["Vocabulary level", profile.vocabulary_level],
                ["Use of analogies", profile.analogy_frequency],
                ["Example density", profile.example_density],
              ].map(([label, value]) => (
                <div className="fp-row" key={label}>
                  <div className="fp-top">
                    <span className="fp-label">{label}</span>
                    <span className="fp-scale">{value || "unknown"}</span>
                  </div>
                  <div className="meter">
                    <div
                      className={`meter-fill ${label === "Use of analogies" ? "meter-amber" : ""}`}
                      style={{ width: `${percentFor(value)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="col-side">
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-head"><span className="card-title">How ideas are sequenced</span></div>
                <div className="card-pad" style={{ padding: "16px 18px" }}>
                  <div className="quote">
                    {style.concept_sequencing_notes || "No sequencing notes were returned for this transcript."}
                  </div>
                </div>
              </div>
              {style.signature_phrases?.length > 0 && (
                <div className="card">
                  <div className="card-head"><span className="card-title">Signature phrases</span></div>
                  <div className="phrase-wrap">
                    {style.signature_phrases.map((phrase) => (
                      <span className="chip" key={phrase}>{phrase}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}

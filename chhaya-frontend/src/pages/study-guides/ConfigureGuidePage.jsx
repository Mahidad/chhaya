import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import { TextField, Checkbox } from "../../components/ui/Field";
import { listTeacherProfiles } from "../../api/teacherProfiles"; // <- Mahidad's Feature 3 API, reused directly
import { createStudyGuide } from "../../api/studyGuides";

/*
  THE INTERCONNECTION POINT: this page imports `listTeacherProfiles` from
  Mahidad's `api/teacherProfiles.js` -- the exact same function
  StyleLibraryPage.jsx calls. A study guide cannot be generated without
  picking one of Mahidad's profiles first, so this page IS the proof that
  the two modules connect, not just a description of it.

  Simplified vs. lamia-f1-02-configure.html: no "not covered in your
  reference source" chip (needs course/topic-coverage tracking that
  doesn't exist), no practice-questions checkbox (needs Omar's quiz
  generation), no live credit-usage counter. Topic, style pick, depth,
  formula sheet, and Bangla toggle are all real and wired.
*/

const DEPTH_OPTIONS = [
  { value: "quick", title: "Quick revision", sub: "2 pages, night before the exam" },
  { value: "standard", title: "Standard chapter", sub: "Several sections with worked examples" },
  { value: "deep", title: "Deep dive", sub: "Derivations and proofs included" },
];

export default function ConfigureGuidePage() {
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState(null);
  const [topic, setTopic] = useState("");
  const [profileId, setProfileId] = useState(null);
  const [depth, setDepth] = useState("standard");
  const [includeFormulaSheet, setIncludeFormulaSheet] = useState(false);
  const [includeBangla, setIncludeBangla] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listTeacherProfiles().then((data) => {
      setProfiles(data);
      if (data.length > 0) setProfileId(data[0].id);
    });
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!profileId) {
      setError("Add at least one reference source first — a guide needs a style to write in.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const guide = await createStudyGuide({
        topic,
        teacherProfileId: profileId,
        depth,
        includeFormulaSheet,
        includeBangla,
      });
      navigate(`/guides/${guide.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not generate that guide.");
      setSubmitting(false);
    }
  }

  const selectedProfile = profiles?.find((p) => p.id === profileId);

  return (
    <AppShell section="Study guides" current="New guide">
      <div className="page-head">
        <div>
          <div className="page-title">New study guide</div>
          <div className="page-sub">Three choices: what to learn, whose voice to learn it in, and how you want it delivered.</div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" onClick={() => navigate("/guides")}>Cancel</Button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="split">
        <div className="col-form card">
          <div className="form-grid">
            <TextField
              label="1. Topic"
              icon="search"
              placeholder="Second law of thermodynamics and entropy"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
            />

            <div>
              <div className="label" style={{ marginBottom: 8 }}>2. Teaching style</div>
              {profiles === null ? (
                <div className="hint">Loading your style library...</div>
              ) : profiles.length === 0 ? (
                <div className="hint">
                  Your style library is empty — add a reference source first, Chhaya needs a teacher's voice to write in.
                </div>
              ) : (
                profiles.map((p) => (
                  <div key={p.id} className={`pick-row ${profileId === p.id ? "on" : ""}`} onClick={() => setProfileId(p.id)}>
                    <div className="avatar avatar-sm">{p.display_name.slice(0, 2).toUpperCase()}</div>
                    <div>
                      <div className="pick-name">{p.display_name}</div>
                      <div className="pick-sub">
                        {[p.pacing, p.analogy_frequency && `${p.analogy_frequency} analogies`].filter(Boolean).join(" · ")}
                      </div>
                    </div>
                    <div className="pick-right">
                      <div className={`radio ${profileId === p.id ? "radio-on" : ""}`} />
                    </div>
                  </div>
                ))
              )}
            </div>

            <div>
              <div className="label" style={{ marginBottom: 8 }}>3. Depth and language</div>
              <div className="depth-buttons-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '16px' }}>
                {DEPTH_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setDepth(opt.value)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      padding: '16px',
                      borderRadius: '10px',
                      border: '2px solid ' + (depth === opt.value ? 'var(--primary)' : 'var(--line)'),
                      background: depth === opt.value ? 'var(--primary-soft)' : 'var(--surface)',
                      color: 'var(--ink)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: depth === opt.value ? '0 4px 12px rgba(0, 0, 0, 0.05)' : 'none',
                    }}
                  >
                    <div style={{ fontWeight: '700', fontSize: '14px', color: depth === opt.value ? 'var(--primary-dark)' : 'var(--ink)', marginBottom: '4px' }}>
                      {opt.title}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: '1.4' }}>
                      {opt.sub}
                    </div>
                  </button>
                ))}
              </div>
              <Checkbox
                checked={includeFormulaSheet}
                onChange={() => setIncludeFormulaSheet((v) => !v)}
                label="Add a condensed formula sheet"
                sub="Best for STEM topics."
              />
              <Checkbox
                checked={includeBangla}
                onChange={() => setIncludeBangla((v) => !v)}
                label="Write a Bangla version too"
                sub="Recorded on the guide — translation isn't generated yet, see the frontend README."
              />
            </div>
          </div>
        </div>

        <div className="col-side card">
          <div className="card-head">
            <span className="card-title">Guide summary</span>
            <span className="card-note">Before you generate</span>
          </div>
          <div className="sum-row">
            <span>Topic</span>
            <span className="sum-v" style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {topic || "—"}
            </span>
          </div>
          <div className="sum-row">
            <span>Style</span>
            <span className="sum-v">{selectedProfile?.display_name || "—"}</span>
          </div>
          <div className="sum-row">
            <span>Depth</span>
            <span className="sum-v" style={{ textTransform: 'capitalize' }}>{depth}</span>
          </div>
          <div className="sum-row">
            <span>Formula sheet</span>
            <span className="sum-v">{includeFormulaSheet ? "Yes" : "No"}</span>
          </div>
          <div className="sum-row">
            <span>Bangla version</span>
            <span className="sum-v">{includeBangla ? "Yes" : "No"}</span>
          </div>

          <div className="sum-foot">
            <Button type="submit" disabled={submitting || !topic || !profileId} style={{ width: "100%", justifyContent: "center" }} icon={<Icon name="fileText" size={16} />}>
              {submitting ? "Generating..." : "Generate study guide"}
            </Button>
            {error && <div className="error-text" style={{ marginTop: 8, textAlign: "center" }}>{error}</div>}
          </div>
        </div>
      </form>
    </AppShell>
  );
}

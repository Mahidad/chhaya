import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { TextField, SelectField, Checkbox } from "../../components/ui/Field";
import AnalysingPanel from "../../components/reference-sources/AnalysingPanel";
import { createReferenceSource } from "../../api/referenceSources";

/*
  Matches mahidad-f1-02-add-source.html. Two kinds of fields here, marked
  clearly so nobody on the team mistakes one for the other later:
    - WIRED fields (title, url, source type) actually go to the API.
    - DECORATIVE fields (teacher, course, cleaning options) exist in the
      mockup but the backend doesn't accept them yet -- disabled with a
      "coming soon" hint instead of silently doing nothing when touched.
  Extending the backend's `ReferenceSourceCreate` schema + service to
  accept these is a natural next task once the core loop is solid.
*/
export default function AddSourcePage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [sourceType, setSourceType] = useState("youtube_video");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const source = await createReferenceSource({ title, sourceType, url });
      navigate(`/sources/${source.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add that source. Double-check the link and try again.");
      setSubmitting(false);
    }
  }

  if (submitting) {
    return (
      <AppShell section="Reference sources" current="Analysing">
        <div className="page-head">
          <div>
            <div className="page-title">Reading {title || "your source"}</div>
            <div className="page-sub">Keep this tab open, it runs in the background too.</div>
          </div>
        </div>
        <AnalysingPanel title="Building the style profile" subtitle="This usually takes under a minute" />
      </AppShell>
    );
  }

  return (
    <AppShell section="Reference sources" current="Add source">
      <div className="page-head">
        <div>
          <div className="page-title">Add a reference source</div>
          <div className="page-sub">
            Chhaya reads the captions of this lecture, then writes a style profile from them.
          </div>
        </div>
        <div className="page-actions">
          <Badge variant="primary" icon={<Icon name="fileText" size={12} />}>Draft</Badge>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="split">
        <div className="col-form card">
          <div className="form-grid">
            <TextField
              label="YouTube video link"
              icon="sources"
              placeholder="youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              hint="Public YouTube videos with captions on are supported today. Playlist crawling is on the roadmap."
            />
            <div className="row-2">
              <TextField
                label="Source name"
                placeholder="Data Structures — Lecture 1"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
              <SelectField label="Source type" value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                <option value="youtube_video">Single YouTube video</option>
                <option value="youtube_playlist">YouTube playlist (coming soon)</option>
                <option value="course_link">Course link (coming soon)</option>
              </SelectField>
            </div>

            <div className="row-2" style={{ opacity: 0.55 }}>
              <TextField label="Teacher" placeholder="Coming soon" disabled />
              <TextField label="Course" placeholder="Coming soon" disabled />
            </div>

            <div>
              <div className="label" style={{ marginBottom: 4 }}>How the transcript is cleaned</div>
              <Checkbox
                checked
                onChange={() => {}}
                label="Strip filler words and timestamps"
                sub="Removes “umm”, “so basically”, caption noise."
                right={<span className="badge">Always on</span>}
              />
              <Checkbox
                checked={false}
                onChange={() => {}}
                label="Skip lectures shorter than 3 minutes"
                sub="Coming soon — matters once playlists are supported."
              />
            </div>
          </div>
          <div className="form-foot">
            <Button type="submit" icon={<Icon name="fileText" size={16} />} disabled={submitting}>
              {submitting ? "Starting..." : "Fetch and analyse"}
            </Button>
            <Button type="button" variant="ghost" onClick={() => navigate("/sources")}>
              Cancel
            </Button>
            {error && <div className="error-text" style={{ marginLeft: 8 }}>{error}</div>}
            <div className="credit-note">Runs youtube-transcript-api + Gemini · about a minute</div>
          </div>
        </div>

        <div className="col-side card">
          <div className="card-head">
            <span className="card-title">What happens next</span>
          </div>
          <div className="card-pad" style={{ padding: "16px 18px" }}>
            <div className="vid-row" style={{ borderTop: "none", paddingTop: 0 }}>
              <span className="vid-idx">1</span>
              <span className="vid-name">Transcript is fetched from YouTube's captions.</span>
            </div>
            <div className="vid-row">
              <span className="vid-idx">2</span>
              <span className="vid-name">Gemini reads it and scores pacing, vocabulary, analogies, and examples.</span>
            </div>
            <div className="vid-row">
              <span className="vid-idx">3</span>
              <span className="vid-name">A reusable style profile lands in your library.</span>
            </div>
          </div>
        </div>
      </form>
    </AppShell>
  );
}

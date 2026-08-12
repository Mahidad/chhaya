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

  DUPLICATE-LINK FLOW: submitting a link the backend recognizes as
  already-extracted doesn't fail outright -- the API returns 409 with the
  existing source's name (see app/utils/exceptions.py's
  DuplicateSourceError on the backend). This page catches that
  specifically and shows a confirm dialog instead of a plain error,
  because "already extracted, want to do it again?" is a real choice for
  the student to make, not just a mistake to correct.

  Two kinds of fields, still marked clearly:
    - WIRED fields (title, url, source type, force) go to the API.
    - DECORATIVE fields (teacher, course, cleaning options) exist in the
      mockup but the backend doesn't accept them yet.
*/
export default function AddSourcePage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [sourceType, setSourceType] = useState("youtube_video");
  const [skipShort, setSkipShort] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [duplicateWarning, setDuplicateWarning] = useState(null); // { existingTitle } | null

  async function submit({ force }) {
    setError("");
    setSubmitting(true);
    try {
      const source = await createReferenceSource({ title, sourceType, url, force });
      navigate(`/sources/${source.id}`);
    } catch (err) {
      if (err.response?.status === 409) {
        setSubmitting(false);
        setDuplicateWarning({ existingTitle: err.response.data.detail.existing_title });
        return;
      }
      setError(err.response?.data?.detail || "Could not add that source. Double-check the link and try again.");
      setSubmitting(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    submit({ force: false });
  }

  if (submitting) {
    return (
      <AppShell section="Reference sources" current="Analysing">
        <div className="page-head">
          <div>
            <div className="page-title">Reading {title || "your source"}</div>
            <div className="page-sub">
              {sourceType === "youtube_playlist"
                ? "Grouping videos by instructor and building a style profile per teacher."
                : "Keep this tab open, it runs in the background too."}
            </div>
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
              label={sourceType === "youtube_playlist" ? "YouTube playlist link" : "YouTube video link"}
              icon="sources"
              placeholder={sourceType === "youtube_playlist" ? "youtube.com/playlist?list=..." : "youtube.com/watch?v=..."}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              hint={
                sourceType === "youtube_playlist"
                  ? "If the playlist mixes more than one instructor's videos, Chhaya groups them by channel and builds one style profile per instructor."
                  : "Public YouTube videos with captions on are supported."
              }
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
                <option value="youtube_playlist">YouTube playlist</option>
                <option value="course_link" disabled>Course link (coming soon)</option>
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
                onChange={() => { }}
                label="Strip filler words and timestamps"
                sub="Removes “umm”, “so basically”, caption noise."
                right={<span className="badge">Always on</span>}
              />
              <Checkbox
                checked={skipShort}
                onChange={() => setSkipShort((v) => !v)}
                label="Skip lectures shorter than 3 minutes"
                sub="Skips videos with duration under 180 seconds."
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
              <span className="vid-name">
                {sourceType === "youtube_playlist"
                  ? "Every video's transcript is fetched and grouped by uploader."
                  : "Transcript is fetched from YouTube's captions."}
              </span>
            </div>
            <div className="vid-row">
              <span className="vid-idx">2</span>
              <span className="vid-name">
                {sourceType === "youtube_playlist"
                  ? "Gemini scores style separately for each instructor detected."
                  : "Gemini reads it and scores pacing, vocabulary, analogies, and examples."}
              </span>
            </div>
            <div className="vid-row">
              <span className="vid-idx">3</span>
              <span className="vid-name">
                {sourceType === "youtube_playlist"
                  ? "One reusable style profile per instructor lands in your library."
                  : "A reusable style profile lands in your library."}
              </span>
            </div>
          </div>
        </div>
      </form>

      {duplicateWarning && (
        <div className="overlay" onClick={() => setDuplicateWarning(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-pad">
              <div className="dialog-icon di-primary">
                <Icon name="alertTriangle" size={20} />
              </div>
              <div className="dialog-title">Already extracted</div>
              <div className="dialog-copy">
                This link matches a source you already have — "{duplicateWarning.existingTitle}". Extract it
                again under the name "{title}"?
              </div>
            </div>
            <div className="dialog-foot">
              <Button variant="ghost" onClick={() => setDuplicateWarning(null)}>Cancel</Button>
              <Button
                onClick={() => {
                  setDuplicateWarning(null);
                  submit({ force: true });
                }}
              >
                Extract again
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

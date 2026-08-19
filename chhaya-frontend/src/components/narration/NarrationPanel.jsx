import { useEffect, useRef, useState } from "react";
import Icon from "../icons/Icon";
import Button from "../ui/Button";
import {
  listVoices, listNarrations, createNarration, deleteNarration, getNarrationAudioBlob,
} from "../../api/narrations";
import { listTeacherProfiles } from "../../api/teacherProfiles";

/*
  Module 3 (Lamia): AI Voice Narration (Edge TTS). Embedded as a card
  inside GuideDetailPage.jsx and NoteViewerPage.jsx rather than being its
  own page/route -- a narration is an artifact *of* a piece of content,
  same relationship a highlight or a glossary entry has to it.

  NO MANUAL VOICE PICKER HERE ON PURPOSE: voice (accent/gender) is a
  fixed property of whichever teacher profile is used -- Gemini makes a
  best-effort guess at analysis time (see teaching_style_service.py) and
  the student corrects it once, permanently, in the Style Library if it's
  wrong (see StyleLibraryPage.jsx). That's what actually solves "which
  style was this generated in" -- the teacher's name is shown on every
  narration row below, and the voice is always whatever that teacher's
  profile says it is, not a per-play guess.

  Props:
    contentType, contentId  -- same polymorphic pair used everywhere else
                                (see constants/contentTypes.js)
    guideTeacherProfileId   -- pass this for a study guide (its own style
                                is used automatically, no picker shown).
                                Leave undefined for a note -- the panel
                                will require the student to pick one,
                                since a note has no inherent style.
*/
export default function NarrationPanel({ contentType, contentId, guideTeacherProfileId }) {
  const [voiceLabels, setVoiceLabels] = useState({}); // voice id -> "Aria (US, female)"
  const [narrations, setNarrations] = useState([]);
  const [profiles, setProfiles] = useState(null);
  const [pickedProfileId, setPickedProfileId] = useState("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [audioUrls, setAudioUrls] = useState({}); // narrationId -> blob: URL

  const needsProfilePicker = !guideTeacherProfileId;

  const refresh = () => listNarrations(contentType, contentId).then(setNarrations);

  useEffect(() => {
    listVoices().then((v) => {
      setVoiceLabels(Object.fromEntries(v.map((x) => [x.id, x.label])));
    });
    refresh();
    // Fetched either way -- for a note, this is the required style
    // picker; for a guide, it's only used to look up the teacher's
    // display name to show on each narration row below.
    listTeacherProfiles().then((data) => {
      setProfiles(data);
      if (needsProfilePicker && data.length > 0) setPickedProfileId(data[0].id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentType, contentId]);

  // Poll any narration that's still pending/generating.
  useEffect(() => {
    const active = narrations.some((n) => n.status === "pending" || n.status === "generating");
    if (!active) return;
    const timer = setTimeout(refresh, 2000);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [narrations]);

  // Fetch each ready narration's audio as a blob once, cache the object
  // URL -- see api/narrations.js's docstring for why <audio src> can't
  // just point straight at the backend URL.
  useEffect(() => {
    narrations
      .filter((n) => n.status === "ready" && !audioUrls[n.id])
      .forEach((n) => {
        getNarrationAudioBlob(n.id).then((blob) => {
          setAudioUrls((prev) => ({ ...prev, [n.id]: URL.createObjectURL(blob) }));
        });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [narrations]);

  function teacherNameFor(profileId) {
    return profiles?.find((p) => p.id === profileId)?.display_name || "Unknown style";
  }

  async function handleGenerate() {
    setError("");
    if (needsProfilePicker && !pickedProfileId) {
      setError("Choose a teacher's style to narrate this in.");
      return;
    }
    setGenerating(true);
    try {
      await createNarration({
        contentType, contentId,
        teacherProfileId: needsProfilePicker ? pickedProfileId : guideTeacherProfileId,
      });
      refresh();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not start narration.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleDelete(id) {
    await deleteNarration(id);
    refresh();
  }

  return (
    <div className="card">
      <div className="card-head">
        <span className="card-title">Voice narration</span>
      </div>
      <div className="card-pad" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {needsProfilePicker && (
          <div>
            <div className="label" style={{ marginBottom: 6 }}>Teacher's style</div>
            {profiles === null ? (
              <div className="hint">Loading your style library...</div>
            ) : profiles.length === 0 ? (
              <div className="hint">No teaching styles saved yet -- add a reference source first.</div>
            ) : (
              <select className="select" value={pickedProfileId} onChange={(e) => setPickedProfileId(e.target.value)}>
                {profiles.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}
              </select>
            )}
            <div className="hint" style={{ marginTop: 4 }}>
              Voice and speaking speed are matched to this teacher automatically.
              You can correct the voice for any teacher once, permanently, in the Style Library.
            </div>
          </div>
        )}

        {error && <div className="error-text">{error}</div>}

        <Button size="sm" onClick={handleGenerate} disabled={generating}>
          {generating ? "Starting..." : "Generate narration"}
        </Button>

        {narrations.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 4 }}>
            {narrations.map((n) => (
              <div key={n.id} className="narration-row">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="hint" style={{ marginBottom: 4 }}>
                    <strong>{teacherNameFor(n.teacher_profile_id)}</strong>
                    {" · "}
                    {voiceLabels[n.voice] || n.voice}
                    {n.is_mock && <span className="badge badge-amber" style={{ marginLeft: 6 }}>Mock audio</span>}
                  </div>
                  {n.status === "ready" && audioUrls[n.id] && (
                    <NarrationAudioPlayer src={audioUrls[n.id]} />
                  )}
                  {(n.status === "pending" || n.status === "generating") && (
                    <div className="hint">Generating...</div>
                  )}
                  {n.status === "failed" && (
                    <div className="error-text">{n.error_message || "Narration failed."}</div>
                  )}
                </div>
                <button className="mini-btn" onClick={() => handleDelete(n.id)} title="Delete narration">
                  <Icon name="trash" size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// 1x/2x playback speed toggle. This is deliberately NOT a backend
// feature -- generating two separate audio files at two speeds would
// double edge-tts calls and storage for something the <audio> element
// already does natively via its `playbackRate` property. One saved file,
// the browser plays it back faster on request.
function NarrationAudioPlayer({ src }) {
  const audioRef = useRef(null);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = speed;
  }, [speed, src]);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <audio
        ref={audioRef}
        controls
        src={src}
        style={{ flex: 1, height: 32 }}
        onPlay={(e) => { e.currentTarget.playbackRate = speed; }}
      />
      <div style={{ display: "flex", gap: 4 }}>
        {[1, 2].map((s) => (
          <button
            key={s}
            type="button"
            className={`chip ${speed === s ? "chip-on" : ""}`}
            style={{ padding: "2px 8px", fontSize: 11 }}
            onClick={() => setSpeed(s)}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  );
}

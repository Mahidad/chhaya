import { useEffect, useRef, useState } from "react";
import Button from "../ui/Button";
import Icon from "../icons/Icon";
import {
  findNarration,
  generateNarration,
  narrationAudioUrl,
} from "../../api/voiceNarrations";

/*
  Module 3 Feature 1 (Lamia) -- voice narration for a note or a study guide.

  DROP THIS INTO EITHER PAGE:
    <VoiceNarrationPlayer noteId={note.id} teacherProfiles={profiles} />
    <VoiceNarrationPlayer studyGuideId={guide.id} />

  The teacher-style picker only renders when `noteId` is given. That's the
  spec's rule: a generated study guide is already written in a teacher's
  style, so its narration inherits that same profile and offering a
  different voice would contradict the text. The backend enforces this too
  (it rejects teacher_profile_id alongside study_guide_id), so the UI and
  the API agree rather than relying on the UI alone to prevent it.

  Existing audio is looked up on mount and reused -- generation only
  happens when the student presses the button, or presses Regenerate.
*/
export default function VoiceNarrationPlayer({ noteId, studyGuideId, teacherProfiles = [] }) {
  const [narration, setNarration] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [teacherProfileId, setTeacherProfileId] = useState("");
  const [speed, setSpeed] = useState(1);

  const audioRef = useRef(null);

  useEffect(() => {
    findNarration({ noteId, studyGuideId })
      .then(setNarration)
      .catch(() => setNarration(null))
      .finally(() => setLoading(false));
  }, [noteId, studyGuideId]);

  // Playback rate isn't a normal React-controlled attribute -- it has to
  // be set imperatively on the audio element each time it changes.
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = speed;
  }, [speed, narration]);

  async function handleGenerate(regenerate = false) {
    setGenerating(true);
    setError("");
    try {
      const result = await generateNarration({
        noteId,
        studyGuideId,
        teacherProfileId: noteId ? teacherProfileId : null,
        regenerate,
      });
      setNarration(result);
      if (result.status === "failed") {
        setError(result.error_message || "Voice generation failed.");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not generate narration.");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return <div className="hint">Checking for saved narration...</div>;
  }

  const isReady = narration?.status === "ready";

  return (
    <div className="narration-box">
      <div className="narration-head">
        <Icon name="wand" size={15} />
        <span className="narration-title">Voice narration</span>
        {isReady && narration.voice_short_name && (
          <span className="hint">{narration.voice_short_name}</span>
        )}
      </div>

      {!isReady && (
        <div className="narration-controls">
          {noteId && teacherProfiles.length > 0 && (
            <select
              className="conv-select"
              value={teacherProfileId}
              onChange={(e) => setTeacherProfileId(e.target.value)}
            >
              <option value="">Default voice</option>
              {teacherProfiles.map((p) => (
                <option key={p.id} value={p.id}>{p.display_name}</option>
              ))}
            </select>
          )}
          <Button
            size="sm"
            icon={<Icon name="wand" size={14} />}
            onClick={() => handleGenerate(false)}
            disabled={generating}
          >
            {generating ? "Generating..." : "Generate narration"}
          </Button>
        </div>
      )}

      {isReady && (
        <>
          <audio
            ref={audioRef}
            controls
            src={narrationAudioUrl(narration.id)}
            style={{ width: "100%", marginTop: 10 }}
          />
          <div className="narration-controls">
            <span className="hint">Speed</span>
            {[1, 2].map((s) => (
              <button
                key={s}
                className={`speed-btn ${speed === s ? "speed-btn-on" : ""}`}
                onClick={() => setSpeed(s)}
              >
                {s}x
              </button>
            ))}
            <Button
              size="sm"
              variant="ghost"
              icon={<Icon name="refresh" size={14} />}
              onClick={() => handleGenerate(true)}
              disabled={generating}
              style={{ marginLeft: "auto" }}
            >
              {generating ? "Regenerating..." : "Regenerate"}
            </Button>
          </div>
        </>
      )}

      {error && <div className="error-text" style={{ marginTop: 8 }}>{error}</div>}
    </div>
  );
}

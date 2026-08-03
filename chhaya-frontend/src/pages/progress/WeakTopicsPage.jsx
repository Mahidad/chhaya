import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Badge from "../../components/ui/Badge";
import Icon from "../../components/icons/Icon";
import { TextField } from "../../components/ui/Field";
import { getWeakTopics, recordQuizResult } from "../../api/progress";

/*
  No mockup exists for this screen (Amiyo's Module 1 feature wasn't in
  the Figma export) -- built functional-first, matching existing classes
  (.card, .topic-row, badges) rather than inventing new visual language.
  Worth a real design pass.

  The "log a result" form below exists ONLY because nothing else in the
  app writes to quiz_results yet -- see the note in
  app/services/progress_service.py. Once Omar's quiz feature (Module 3)
  exists and calls POST /progress/quiz-results itself, this manual form
  can be deleted; the dashboard logic below it doesn't change at all.
*/
export default function WeakTopicsPage() {
  const [topics, setTopics] = useState(null);
  const [topic, setTopic] = useState("");
  const [score, setScore] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const refresh = () => getWeakTopics().then(setTopics);

  useEffect(() => {
    refresh();
  }, []);

  async function handleLog(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await recordQuizResult({ topic, scorePercent: Number(score) });
      setTopic("");
      setScore("");
      refresh();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell section="Overview" current="Weak topics">
      <div className="page-head">
        <div>
          <div className="page-title">Weak learning areas</div>
          <div className="page-sub">Topics averaging below 60% across your quiz attempts, weakest first.</div>
        </div>
      </div>

      <div className="split">
        <div className="col-form card">
          {topics === null ? (
            <div className="card-pad" style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>
          ) : topics.length === 0 ? (
            <div className="card-pad" style={{ color: "var(--muted)", fontSize: 13 }}>
              No quiz results recorded yet. Log one on the right to see the dashboard work.
            </div>
          ) : (
            topics.map((t) => (
              <div className="topic-row" key={t.topic}>
                <div className="topic-name">
                  {t.topic}
                  {t.course && <span style={{ color: "var(--faint)", fontWeight: 400 }}> · {t.course}</span>}
                </div>
                <div style={{ flex: 1, maxWidth: 200 }}>
                  <div className="meter">
                    <div
                      className={`meter-fill ${t.is_weak ? "meter-amber" : ""}`}
                      style={{ width: `${t.average_score}%`, background: t.is_weak ? "var(--danger)" : "var(--ok)" }}
                    />
                  </div>
                </div>
                <div className="topic-score">{t.average_score}%</div>
                <Badge variant={t.is_weak ? "danger" : "ok"}>{t.is_weak ? "Needs work" : "Solid"}</Badge>
                <span className="hint">{t.attempts} attempt{t.attempts === 1 ? "" : "s"}</span>
              </div>
            ))
          )}
        </div>

        <div className="col-side card">
          <div className="card-head"><span className="card-title">Log a quiz result</span></div>
          <form onSubmit={handleLog} className="form-grid" style={{ padding: "16px 18px" }}>
            <TextField label="Topic" placeholder="AVL rotations" value={topic} onChange={(e) => setTopic(e.target.value)} required />
            <TextField label="Score (%)" type="number" min="0" max="100" placeholder="55" value={score} onChange={(e) => setScore(e.target.value)} required />
            <Button type="submit" disabled={submitting} icon={<Icon name="check" size={16} />}>
              {submitting ? "Saving..." : "Log result"}
            </Button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}

import Icon from "../icons/Icon";

/*
  Matches the visual language of mahidad-f1-03-analysing.html, with one
  deliberate simplification: the mockup shows five steps with live
  per-lecture percentages, because it assumes a background worker
  streaming granular progress. The current backend (see
  reference_source_service.create_and_process's docstring) runs ingestion
  synchronously inside one request-response, so the frontend only knows
  "in progress" vs "done" -- not which of 5 sub-steps it's on. Rather than
  fabricate a percentage the backend isn't actually reporting, this shows
  an honest indeterminate state. Once ingestion moves to a background
  task that updates status incrementally, this is the component to expand
  back into the full 5-step breakdown -- the visual shell already matches.
*/
export default function AnalysingPanel({ title, subtitle }) {
  return (
    <div className="split">
      <div className="col-form card">
        <div className="gen-head">
          <div>
            <div className="card-title">{title}</div>
            <div className="hint" style={{ marginTop: 3 }}>{subtitle}</div>
          </div>
        </div>
        <div className="card-pad" style={{ padding: "0 20px 20px" }}>
          <div className="progress" style={{ margin: "16px 0 4px" }}>
            <div
              className="progress-fill"
              style={{ width: "45%", animation: "chhaya-indeterminate 1.4s ease-in-out infinite" }}
            />
          </div>
          <style>{`
            @keyframes chhaya-indeterminate {
              0% { margin-left: 0%; width: 20%; }
              50% { margin-left: 60%; width: 35%; }
              100% { margin-left: 0%; width: 20%; }
            }
          `}</style>

          <div className="step">
            <div className="step-mark step-live"><Icon name="fileText" size={13} /></div>
            <div>
              <div className="step-name">Fetching transcript</div>
              <div className="step-meta">youtube-transcript-api</div>
            </div>
            <div className="step-right" style={{ color: "var(--amber)" }}>In progress</div>
          </div>
          <div className="step" style={{ borderBottom: "none" }}>
            <div className="step-mark step-wait">2</div>
            <div>
              <div className="step-name waiting">Analysing teaching style</div>
              <div className="step-meta">Pacing, vocabulary, analogies, example density · Gemini</div>
            </div>
            <div className="step-right">Queued</div>
          </div>
        </div>
      </div>
      <div className="col-side card">
        <div className="card-head"><span className="card-title">Good to know</span></div>
        <div className="card-pad" style={{ padding: "16px 18px", fontSize: 12, color: "var(--muted)", lineHeight: 1.7 }}>
          This usually takes under a minute for a single lecture. Keep this
          tab open — closing it doesn't cancel the run, but you'll need to
          come back to this page to see the result.
        </div>
      </div>
    </div>
  );
}

/*
  The "simple variable-watch table" chosen for the Visualizer's launch
  scope: shows every variable's value at the current step, plus the
  step's short description. Deliberately not a graphical box-and-arrow
  rendering (that's a larger future build) -- this is the fast-to-build
  version that's still genuinely useful for seeing state change line by
  line.
*/
export default function VariableWatchTable({ step }) {
  if (!step) return null;

  const entries = Object.entries(step.variables || {});

  return (
    <div className="var-watch">
      <div className="var-watch-title">Variables at this step</div>
      {entries.length === 0 ? (
        <div className="hint">No variables in scope yet.</div>
      ) : (
        <div className="var-watch-grid">
          {entries.map(([name, value]) => (
            <div className="var-watch-cell" key={name}>
              <div className="var-watch-name">{name}</div>
              <div className="var-watch-value">{String(value)}</div>
            </div>
          ))}
        </div>
      )}
      {step.description && (
        <div className="hint" style={{ marginTop: 10 }}>{step.description}</div>
      )}
    </div>
  );
}

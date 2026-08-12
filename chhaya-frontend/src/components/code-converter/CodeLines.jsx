/*
  Renders code as individually clickable lines, and highlights whichever
  range is "active" -- this is the mechanism behind "click a line in the
  source, see the matching lines in the output light up". The parent page
  owns the active range (derived from a mapping block returned by the
  backend, see CodeConverterPage.jsx); this component just renders it and
  reports clicks.

  Line numbers are 1-indexed everywhere in this feature (state, API
  responses, this component) to match how a human reads a file and how
  the backend's line ranges are defined -- converting back and forth
  between 0-indexed arrays and 1-indexed line numbers is exactly the kind
  of off-by-one bug worth avoiding by just being consistent everywhere.
*/
export default function CodeLines({ code, activeRange, onLineClick }) {
  const lines = (code || "").split("\n");

  return (
    <div className="code-lines">
      {lines.map((line, idx) => {
        const lineNum = idx + 1;
        const isActive = activeRange && lineNum >= activeRange[0] && lineNum <= activeRange[1];
        return (
          <div
            key={idx}
            className={`code-line ${isActive ? "code-line-active" : ""}`}
            onClick={() => onLineClick(lineNum)}
          >
            <span className="code-line-num">{lineNum}</span>
            <span className="code-line-text">{line.length ? line : " "}</span>
          </div>
        );
      })}
    </div>
  );
}

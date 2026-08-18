import { useEffect, useState } from "react";
import Badge from "../ui/Badge";
import Icon from "../icons/Icon";
import { getPracticeDashboard } from "../../api/practice";

/*
  Code Studio's dashboard. Every number here comes from
  practice_dashboard_service.py, which is pure aggregation over the
  student's own practice_attempts rows -- no AI involved, so this works
  identically with or without a Gemini key.

  Charts are hand-rolled SVG/divs rather than a charting library: two
  simple charts don't justify adding a dependency, and this way the
  styling matches the rest of the app's design tokens exactly.
*/

function formatDuration(seconds) {
  if (seconds == null) return "--";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export default function DashboardPane() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getPracticeDashboard()
      .then(setData)
      .catch(() => setError("Could not load dashboard."));
  }, []);

  if (error) return <div className="error-text">{error}</div>;
  if (!data) return <div style={{ color: "var(--muted)", fontSize: 13 }}>Loading...</div>;

  const hasActivity = data.total_attempted > 0;

  return (
    <div>
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{data.total_solved}</div>
          <div className="stat-label">Problems solved</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data.accuracy_percent}%</div>
          <div className="stat-label">Accuracy</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{formatDuration(data.avg_seconds_to_solve)}</div>
          <div className="stat-label">Avg time to solve</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data.total_attempted}</div>
          <div className="stat-label">Total attempts</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="rank-card">
          <div className="avatar avatar-lg av-amber"><Icon name="pin" size={20} /></div>
          <div>
            <div className="rank-label">{data.rank_label}</div>
            <div className="hint">{data.rank_points} points</div>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
            {Object.entries(data.by_difficulty).map(([diff, count]) => (
              <Badge key={diff} className={`diff-${diff}`}>{count} {diff}</Badge>
            ))}
          </div>
        </div>
      </div>

      {!hasActivity ? (
        <div className="list-card">
          <div className="lib-empty">
            <div className="lib-empty-title">No practice yet</div>
            <div className="lib-empty-copy">
              Solve a problem from the Practice tab and your progress will start showing up here.
            </div>
          </div>
        </div>
      ) : (
        <>
          <GrowthChart growth={data.growth} />
          <ActivityChart activity={data.activity} />
        </>
      )}
    </div>
  );
}

function GrowthChart({ growth }) {
  const max = Math.max(...growth.map((g) => g.cumulative), 1);
  const width = 600;
  const height = 120;
  const stepX = growth.length > 1 ? width / (growth.length - 1) : width;

  const points = growth
    .map((g, i) => `${i * stepX},${height - (g.cumulative / max) * height}`)
    .join(" ");

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-head">
        <span className="card-title">Growth</span>
        <span className="card-note">Cumulative problems solved, last 12 weeks</span>
      </div>
      <div className="chart-box">
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: 130 }} preserveAspectRatio="none">
          <polyline
            points={points}
            fill="none"
            stroke="var(--primary)"
            strokeWidth="2.5"
            vectorEffect="non-scaling-stroke"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        </svg>
        <div className="chart-axis">
          <span>{growth[0]?.week}</span>
          <span>{growth[growth.length - 1]?.week}</span>
        </div>
      </div>
    </div>
  );
}

function ActivityChart({ activity }) {
  const max = Math.max(...activity.map((a) => a.minutes), 1);

  return (
    <div className="card">
      <div className="card-head">
        <span className="card-title">Practice activity</span>
        <span className="card-note">Minutes per day, this month</span>
      </div>
      <div className="chart-box">
        <div className="bar-chart">
          {activity.map((a) => (
            <div
              key={a.date}
              className={`bar-col ${a.minutes > 0 ? "bar-col-filled" : ""}`}
              style={{ height: `${Math.max(2, (a.minutes / max) * 100)}%` }}
              title={`${a.date}: ${a.minutes} min`}
            />
          ))}
        </div>
        <div className="chart-axis">
          <span>Day 1</span>
          <span>Day {activity.length}</span>
        </div>
      </div>
    </div>
  );
}

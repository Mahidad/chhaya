/**
 * AnalyticsDashboardPage.jsx
 * Amiyo Bhowmik – Module 1 Feature 4: Analytics Dashboard
 *
 * What this page shows
 * --------------------
 *  • Summary cards : this week's sessions, study time, and guide views
 *  • Trend banners : human-readable week-over-week comparison strings
 *  • 3 bar charts  : sessions per day / study time per day / guide views per day
 *                    (last 14 days, rendered as inline SVG — no library needed)
 *
 * What is a "study session"?
 * --------------------------
 *  A session = one continuous visit to Chhaya by a logged-in student.
 *  It starts automatically when the app loads (SessionTracker.jsx mounts)
 *  and ends when the student closes the tab or leaves.
 *  Duration is measured in seconds. Sessions ≥ 5 seconds are recorded.
 *
 * How the frontend receives and displays analytics data
 * -----------------------------------------------------
 *  1. On mount → two parallel API calls:
 *       GET /progress/analytics/summary   → cards + trend strings
 *       GET /progress/analytics/chart-data → array of ChartDay objects
 *  2. FastAPI → analytics_service.py → analytics_repository.py (raw SQL)
 *  3. React stores the result in state and renders summary cards + SVG bars.
 */

import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import { getAnalyticsSummary, getChartData, seedSampleData, clearSeedData } from "../../api/progress";

export default function AnalyticsDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [seeding, setSeeding] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [activeSessionMinutes, setActiveSessionMinutes] = useState(0);

  function refreshActiveSessionMinutes() {
    const lastHeartbeat = Number(sessionStorage.getItem("chhaya_last_heartbeat_ms"));
    const startedAt = Number(sessionStorage.getItem("chhaya_session_start_ms"));

    // Use the last heartbeat as the baseline when available.
    // totals.study_minutes from the DB already includes everything up to
    // the last heartbeat, so we only count the unsaved tail (< 60 s → 0 min)
    // to avoid double-counting that causes skipped-minute jumps.
    const baseline = lastHeartbeat > 0 ? lastHeartbeat : startedAt;

    setActiveSessionMinutes(
      Number.isFinite(baseline) && baseline > 0
        ? Math.floor((Date.now() - baseline) / 60_000)
        : 0
    );
  }

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [sum, chart] = await Promise.all([
        getAnalyticsSummary(),
        getChartData(),
      ]);
      setSummary(sum);
      setChartData(chart);
    } catch {
      setError("Could not load analytics data. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    refreshActiveSessionMinutes();

    // An active session's duration grows while this page is open, so keep
    // the summary and charts current without requiring a page reload.
    const refreshTimer = window.setInterval(() => {
      loadData();
      refreshActiveSessionMinutes();
    }, 30_000);
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") loadData();
      if (document.visibilityState === "visible") refreshActiveSessionMinutes();
    };
    window.addEventListener("chhaya-session-started", refreshActiveSessionMinutes);
    document.addEventListener("visibilitychange", refreshWhenVisible);

    return () => {
      window.clearInterval(refreshTimer);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
      window.removeEventListener("chhaya-session-started", refreshActiveSessionMinutes);
    };
  }, []);

  async function handleSeed() {
    setSeeding(true);
    try { await seedSampleData(); await loadData(); }
    finally { setSeeding(false); }
  }

  async function handleClear() {
    if (!confirm("This will remove seed/demo data only. Your real study sessions and guide views are NOT affected. Continue?")) return;
    setClearing(true);
    try { await clearSeedData(); await loadData(); }
    finally { setClearing(false); }
  }

  // ── Loading / error states ─────────────────────────────────────────────────
  if (loading) {
    return (
      <AppShell section="Overview" current="Analytics">
        <DashboardHeader />
        <div className="card card-pad" style={{ color: "var(--muted)", fontSize: 13 }}>Loading analytics…</div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell section="Overview" current="Analytics">
        <DashboardHeader />
        <div className="card card-pad" style={{ color: "var(--danger)", fontSize: 13 }}>{error}</div>
      </AppShell>
    );
  }

  const hasAnyData = chartData?.some((d) => d.session_count > 0 || d.guide_views > 0 || d.study_minutes > 0);
  const totals = summary?.this_week ?? { sessions: 0, guide_views: 0, study_minutes: 0 };
  const tw = { ...totals, study_minutes: totals.study_minutes + activeSessionMinutes };

  return (
    <AppShell section="Overview" current="Analytics">
      {/* ── Page header ────────────────────────────────────────────────────── */}
      <div className="page-head">
        <div>
          <div className="page-title">Learning analytics</div>
          <div className="page-sub">
            Your study activity for this week (Mon – today) vs. last week.
            Sessions are tracked automatically — each app visit counts as one session.
          </div>
        </div>
        <div className="page-actions">
          {/* Clear button — shown even with no data so you can reset after seed */}
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleClear}
            disabled={clearing}
            title="Remove demo seed data only — your real sessions and guide views are kept"
          >
            {clearing ? "Removing…" : "Remove seed data"}
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={handleSeed}
            disabled={seeding}
            title="Insert 14 days of demo data (dev only)"
          >
            {seeding ? "Seeding…" : "Seed demo data"}
          </button>
        </div>
      </div>

      {/* ── Summary cards ──────────────────────────────────────────────────── */}
      <div className="analytics-summary-row">
        <SummaryCard
          label="Sessions this week"
          value={tw.sessions}
          unit="sessions"
          trend={summary?.trend_sessions}
          hint="Each app visit = 1 session"
        />
        <SummaryCard
          label="Study time this week"
          value={tw.study_minutes}
          unit="min"
          trend={summary?.trend_minutes}
          hint="Total minutes across all sessions"
        />
        <SummaryCard
          label="Guide views this week"
          value={tw.guide_views}
          unit="views"
          trend={summary?.trend_guides}
          hint="Times you opened a completed guide"
        />
      </div>

      {/* ── Empty state ────────────────────────────────────────────────────── */}
      {!hasAnyData && (
        <div className="card card-pad" style={{ color: "var(--muted)", fontSize: 13, marginTop: 16 }}>
          No study activity recorded yet. Open a study guide to log a view, start a new session
          by navigating the app, or click <strong>Seed demo data</strong> to preview the dashboard.
        </div>
      )}

      {/* ── Charts — 3 equal columns ──────────────────────────────────────── */}
      {hasAnyData && (
        <div className="split" style={{ marginTop: 16 }}>
          {/* Sessions per day */}
          <div className="card" style={{ flex: "1 1 280px", minWidth: 0 }}>
            <div className="card-head">
              <span className="card-title">Sessions</span>
              <span className="card-note">per day · 14 days</span>
            </div>
            <div style={{ padding: "16px 18px 20px" }}>
              <BarChart
                data={chartData}
                valueKey="session_count"
                color="var(--primary)"
                emptyLabel="No sessions yet"
              />
            </div>
          </div>

          {/* Study time per day */}
          <div className="card" style={{ flex: "1 1 280px", minWidth: 0 }}>
            <div className="card-head">
              <span className="card-title">Study time</span>
              <span className="card-note">minutes/day · 14 days</span>
            </div>
            <div style={{ padding: "16px 18px 20px" }}>
              <BarChart
                data={chartData}
                valueKey="study_minutes"
                color="var(--amber)"
                emptyLabel="No study time yet"
              />
            </div>
          </div>

          {/* Guide views per day */}
          <div className="card" style={{ flex: "1 1 280px", minWidth: 0 }}>
            <div className="card-head">
              <span className="card-title">Guide views</span>
              <span className="card-note">per day · 14 days</span>
            </div>
            <div style={{ padding: "16px 18px 20px" }}>
              <BarChart
                data={chartData}
                valueKey="guide_views"
                color="var(--iris)"
                emptyLabel="No guide views yet"
              />
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

/* ── Shared page header (used in loading/error states too) ─────────────────── */
function DashboardHeader() {
  return (
    <div className="page-head">
      <div>
        <div className="page-title">Learning analytics</div>
        <div className="page-sub">Your study activity over time.</div>
      </div>
    </div>
  );
}

/* ── Summary card ──────────────────────────────────────────────────────────── */
function SummaryCard({ label, value, unit, trend, hint }) {
  let trendColor = "var(--muted)";
  if (trend?.includes("more")) trendColor = "var(--ok)";
  if (trend?.includes("fewer")) trendColor = "var(--danger)";

  return (
    <div className="card card-pad analytics-summary-card">
      <div className="analytics-card-label">{label}</div>
      <div className="analytics-card-value">
        {value}
        <span className="analytics-card-unit">{unit}</span>
      </div>
      {trend && (
        <div className="analytics-card-trend" style={{ color: trendColor }}>
          {trend}
        </div>
      )}
      {hint && (
        <div className="hint" style={{ marginTop: 6 }}>{hint}</div>
      )}
    </div>
  );
}

/* ── SVG bar chart ─────────────────────────────────────────────────────────── */
/**
 * Renders a simple bar chart as inline SVG — no chart library needed.
 * Each bar = one calendar day. Height is proportional to the max value.
 *
 * Props:
 *   data      – ChartDay[] (14 items from the API)
 *   valueKey  – "session_count" | "study_minutes" | "guide_views"
 *   color     – CSS color string
 *   emptyLabel – message shown when all values are 0
 */
function BarChart({ data, valueKey, color, emptyLabel }) {
  if (!data || data.length === 0) return null;

  const values = data.map((d) => d[valueKey]);
  const maxVal = Math.max(...values, 1);

  if (values.every((v) => v === 0)) {
    return (
      <div style={{ color: "var(--faint)", fontSize: 12, textAlign: "center", padding: "24px 0" }}>
        {emptyLabel}
      </div>
    );
  }

  const chartH = 120;
  const barW = 14;
  const gap = 4;
  const totalW = data.length * (barW + gap) - gap;
  const labelH = 18;

  return (
    <svg
      viewBox={`0 0 ${totalW} ${chartH + labelH}`}
      style={{ width: "100%", display: "block", overflow: "visible" }}
      aria-label="Bar chart"
    >
      {data.map((d, i) => {
        const barH = Math.max(Math.round((d[valueKey] / maxVal) * chartH), d[valueKey] > 0 ? 3 : 0);
        const x = i * (barW + gap);
        const y = chartH - barH;
        const showLabel = i % 2 === 0;
        const shortDate = d.day.slice(5); // "MM-DD"

        return (
          <g key={d.day}>
            <rect x={x} y={y} width={barW} height={barH} rx={3} fill={color} opacity={barH === 0 ? 0 : 0.85} />
            {d[valueKey] > 0 && (
              <text x={x + barW / 2} y={y - 3} textAnchor="middle" fontSize={8} fill="var(--ink-2)">
                {d[valueKey]}
              </text>
            )}
            {showLabel && (
              <text x={x + barW / 2} y={chartH + labelH - 2} textAnchor="middle" fontSize={7.5} fill="var(--faint)">
                {shortDate}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

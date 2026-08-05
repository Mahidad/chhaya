/**
 * API helpers for Amiyo's Module 1 Feature 4 – Analytics Dashboard.
 *
 * What each function calls:
 *   startStudySession()           → POST /progress/study-sessions/start
 *   endStudySession(id, secs)     → PUT  /progress/study-sessions/{id}/end
 *   recordGuideView(guideId)      → POST /progress/study-guide-views
 *   getAnalyticsSummary()         → GET  /progress/analytics/summary
 *   getChartData()                → GET  /progress/analytics/chart-data
 *   seedSampleData()              → POST /progress/seed-sample-data  (dev only)
 */

import client from "./client";

/** Start a new study session. Returns { id, started_at, ... } */
export async function startStudySession() {
  const { data } = await client.post("/progress/study-sessions/start");
  return data;
}

/** Close an existing session with the duration in seconds. */
export async function endStudySession(sessionId, durationSecs) {
  const { data } = await client.put(
    `/progress/study-sessions/${sessionId}/end`,
    { duration_secs: durationSecs }
  );
  return data;
}

/**
 * Record that the current user viewed a study guide.
 * Called fire-and-forget from GuideDetailPage — errors are swallowed so
 * a tracking failure never breaks the guide view itself.
 */
export async function recordGuideView(studyGuideId) {
  const { data } = await client.post("/progress/study-guide-views", {
    study_guide_id: studyGuideId,
  });
  return data;
}

/**
 * Fetch this-week / last-week totals and trend sentences.
 * Returns an AnalyticsSummary object.
 */
export async function getAnalyticsSummary() {
  const { data } = await client.get("/progress/analytics/summary");
  return data;
}

/**
 * Fetch per-day chart data for the last 14 days.
 * Returns an array of ChartDay objects:
 *   [{ day, session_count, guide_views, study_minutes }, ...]
 */
export async function getChartData() {
  const { data } = await client.get("/progress/analytics/chart-data");
  return data;
}

/** DEV ONLY – seed 14 days of demo data for the current user. */
export async function seedSampleData() {
  const { data } = await client.post("/progress/seed-sample-data");
  return data;
}

/** DEV ONLY – wipe all analytics data for the current user (reset to clean slate). */
export async function clearSeedData() {
  const { data } = await client.delete("/progress/seed-sample-data");
  return data;
}

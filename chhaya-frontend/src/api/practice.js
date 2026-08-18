import client from "./client";

export async function listPracticeProblems(difficulty) {
  const { data } = await client.get("/practice/problems", {
    params: difficulty ? { difficulty } : {},
  });
  return data;
}

export async function suggestProblems({ folderId, difficulty, limit = 5 }) {
  // Returns [{ problem: {...}, reason: "why this fits your work" }]
  const { data } = await client.post("/practice/suggest", {
    folder_id: folderId,
    difficulty,
    limit,
  });
  return data;
}

export async function startAttempt({ problemId, folderId }) {
  // The clock starts server-side here -- started_at comes back from the
  // backend and is the source of truth for elapsed time, not a local timer.
  const { data } = await client.post("/practice/attempts", {
    problem_id: problemId,
    folder_id: folderId || null,
  });
  return data;
}

export async function submitAttempt(attemptId, { submittedCode, language }) {
  const { data } = await client.post(`/practice/attempts/${attemptId}/submit`, {
    submitted_code: submittedCode,
    language,
  });
  return data;
}

export async function listAttempts() {
  const { data } = await client.get("/practice/attempts");
  return data;
}

export async function getPracticeDashboard() {
  const { data } = await client.get("/practice/dashboard");
  return data;
}

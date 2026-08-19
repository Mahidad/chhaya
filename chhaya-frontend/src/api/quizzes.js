/** Frontend API helpers for Amiyo's Module 3 Feature 7 – Quiz Generation. */

import client from "./client";


/** Generate a quiz from notes for a chapter. Returns quiz + questions. */
export async function generateQuiz(chapterId, numQuestions, marksPerQuestion, difficulty) {
  const { data } = await client.post("/quizzes/generate", {
    chapter_id: chapterId,
    num_questions: numQuestions,
    marks_per_question: marksPerQuestion,
    difficulty: difficulty,
  });
  return data;
}


/** List all quizzes for the current student. */
export async function listQuizzes() {
  const { data } = await client.get("/quizzes");
  return data;
}


/** Get one quiz with its questions. */
export async function getQuizDetail(quizId) {
  const { data } = await client.get(`/quizzes/${quizId}`);
  return data;
}


/** Start the quiz session — backend records started_at and returns ends_at. */
export async function startQuiz(quizId) {
  const { data } = await client.post(`/quizzes/${quizId}/start`);
  return data;
}


/** Submit answers. Backend decides submitted vs auto_submitted based on server time. */
export async function submitQuiz(quizId, answers) {
  // answers = [{ question_id, answer_text }, ...]
  const { data } = await client.post(`/quizzes/${quizId}/submit`, { answers });
  return data;
}


/** Delete a quiz and all its questions. */
export async function deleteQuiz(quizId) {
  await client.delete(`/quizzes/${quizId}`);
}


// ── Feature 8 ──────────────────────────────────────────────────────────────

/** Grade a submitted quiz using Gemini. Returns the full graded result. */
export async function gradeQuiz(quizId) {
  const { data } = await client.post(`/quizzes/${quizId}/grade`);
  return data;
}

/** Get the already-graded results for a quiz. */
export async function getQuizResults(quizId) {
  const { data } = await client.get(`/quizzes/${quizId}/results`);
  return data;
}

/** Retry: generate a new quiz for the same chapter and settings. */
export async function retryQuiz(quizId) {
  const { data } = await client.post(`/quizzes/${quizId}/retry`);
  return data;
}


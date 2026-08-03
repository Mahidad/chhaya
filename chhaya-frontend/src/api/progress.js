import client from "./client";

export async function getWeakTopics() {
  const { data } = await client.get("/progress/weak-topics");
  return data;
}

export async function recordQuizResult({ topic, course, scorePercent }) {
  const { data } = await client.post("/progress/quiz-results", {
    topic,
    course,
    score_percent: scorePercent,
  });
  return data;
}

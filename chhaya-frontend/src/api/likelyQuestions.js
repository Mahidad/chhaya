import client from "./client";

export async function listLikelyQuestionSets() {
  const { data } = await client.get("/likely-questions");
  return data;
}

export async function getLikelyQuestionSet(id) {
  const { data } = await client.get(`/likely-questions/${id}`);
  return data;
}

export async function createLikelyQuestionSet({ title, course, examPaperIds, questionCount }) {
  const { data } = await client.post("/likely-questions", {
    title,
    course: course || null,
    exam_paper_ids: examPaperIds,
    question_count: questionCount,
  });
  return data;
}

export async function deleteLikelyQuestionSet(id) {
  await client.delete(`/likely-questions/${id}`);
}

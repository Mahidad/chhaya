import client from "./client";

/*
  Module 3 (Lamia): Concept Map active-recall game.
*/

export async function listConceptMaps(chapterId) {
  const params = chapterId ? { chapter_id: chapterId } : undefined;
  const { data } = await client.get("/concept-maps", { params });
  return data;
}

export async function createConceptMap({ title, extractionMode, chapterId, sourceStudyGuideId, rawText }) {
  const { data } = await client.post("/concept-maps", {
    title,
    extraction_mode: extractionMode,
    chapter_id: chapterId || null,
    source_study_guide_id: sourceStudyGuideId || null,
    raw_text: rawText || null,
  });
  return data;
}

export async function getConceptMap(mapId) {
  const { data } = await client.get(`/concept-maps/${mapId}`);
  return data;
}

export async function deleteConceptMap(mapId) {
  await client.delete(`/concept-maps/${mapId}`);
}

export async function recordAttempt(mapId, { correctCount, totalCount }) {
  const { data } = await client.post(`/concept-maps/${mapId}/attempts`, {
    correct_count: correctCount,
    total_count: totalCount,
  });
  return data;
}

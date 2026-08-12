import client from "./client";

export async function listStudyGuides() {
  const { data } = await client.get("/study-guides");
  return data;
}

export async function getStudyGuide(id) {
  const { data } = await client.get(`/study-guides/${id}`);
  return data;
}

export async function createStudyGuide({ topic, teacherProfileId, depth, includeFormulaSheet, includeBangla }) {
  const { data } = await client.post("/study-guides", {
    topic,
    teacher_profile_id: teacherProfileId,
    depth,
    include_formula_sheet: includeFormulaSheet,
    include_bangla: includeBangla,
  });
  return data;
}

export async function deleteStudyGuide(id) {
  await client.delete(`/study-guides/${id}`);
}

export async function renameStudyGuide(id, topic) {
  const { data } = await client.patch(`/study-guides/${id}`, { topic });
  return data;
}

export async function fileStudyGuide(id, chapterId) {
  const { data } = await client.patch(`/study-guides/${id}`, { chapter_id: chapterId });
  return data;
}

export async function unfileStudyGuide(id) {
  const { data } = await client.patch(`/study-guides/${id}`, { chapter_id: "NONE" });
  return data;
}

export async function updateStudyGuideContent(id, { content, formulaSheetContent }) {
  const payload = {};
  if (content !== undefined) payload.content = content;
  if (formulaSheetContent !== undefined) payload.formula_sheet_content = formulaSheetContent;
  const { data } = await client.patch(`/study-guides/${id}`, payload);
  return data;
}

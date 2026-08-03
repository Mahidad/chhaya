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

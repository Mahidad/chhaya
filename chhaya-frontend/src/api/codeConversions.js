import client from "./client";

export async function translateCode({ sourceCode, sourceLanguage, targetLanguage, codeStyleProfileId, folderId }) {
  const { data } = await client.post("/code-conversions/translate", {
    source_code: sourceCode,
    source_language: sourceLanguage || null, // null = ask the backend to auto-detect
    target_language: targetLanguage,
    code_style_profile_id: codeStyleProfileId || null,
    folder_id: folderId || null,
  });
  return data;
}

export async function solveProblem({ problemStatement, targetLanguage, codeStyleProfileId, folderId }) {
  const { data } = await client.post("/code-conversions/solve", {
    problem_statement: problemStatement,
    target_language: targetLanguage,
    code_style_profile_id: codeStyleProfileId || null,
    folder_id: folderId || null,
  });
  return data;
}

export async function listConversions() {
  const { data } = await client.get("/code-conversions");
  return data;
}

export async function updateConversion(id, changes) {
  // changes: { title?, is_favorite?, folder_id? } -- partial, same PATCH
  // shape used everywhere else (see teacherProfiles.js for the pattern).
  const { data } = await client.patch(`/code-conversions/${id}`, changes);
  return data;
}

export async function deleteConversion(id) {
  await client.delete(`/code-conversions/${id}`);
}

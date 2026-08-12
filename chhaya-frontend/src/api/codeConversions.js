import client from "./client";

export async function translateCode({ sourceCode, sourceLanguage, targetLanguage, codeStyleProfileId }) {
  const { data } = await client.post("/code-conversions/translate", {
    source_code: sourceCode,
    source_language: sourceLanguage || null, // null = ask the backend to auto-detect
    target_language: targetLanguage,
    code_style_profile_id: codeStyleProfileId || null,
  });
  return data;
}

export async function solveProblem({ problemStatement, targetLanguage, codeStyleProfileId }) {
  const { data } = await client.post("/code-conversions/solve", {
    problem_statement: problemStatement,
    target_language: targetLanguage,
    code_style_profile_id: codeStyleProfileId || null,
  });
  return data;
}

export async function listConversions() {
  const { data } = await client.get("/code-conversions");
  return data;
}

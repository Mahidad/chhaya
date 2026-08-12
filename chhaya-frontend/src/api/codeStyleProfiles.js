import client from "./client";

export async function listCodeStyleProfiles() {
  const { data } = await client.get("/code-style-profiles");
  return data;
}

export async function createCodeStyleProfile({ label, language, sampleCode }) {
  // No loading/polling needed here -- unlike everything else in this app,
  // this runs the crude regex-based analyzer (app/utils/code_style_analyzer.py),
  // not a Gemini call, so the response comes back immediately.
  const { data } = await client.post("/code-style-profiles", {
    label,
    language,
    sample_code: sampleCode,
  });
  return data;
}

export async function updateCodeStyleProfile(id, changes) {
  const { data } = await client.patch(`/code-style-profiles/${id}`, changes);
  return data;
}

export async function deleteCodeStyleProfile(id) {
  await client.delete(`/code-style-profiles/${id}`);
}

import client from "./client";

export async function visualizeCode({ sourceCode, language, folderId }) {
  const { data } = await client.post("/code-visualizations", {
    source_code: sourceCode,
    language,
    folder_id: folderId || null,
  });
  return data;
}

export async function listVisualizations() {
  const { data } = await client.get("/code-visualizations");
  return data;
}

export async function updateVisualization(id, changes) {
  const { data } = await client.patch(`/code-visualizations/${id}`, changes);
  return data;
}

export async function deleteVisualization(id) {
  await client.delete(`/code-visualizations/${id}`);
}

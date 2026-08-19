import client from "./client";

export async function listConceptMaps() {
  const { data } = await client.get("/concept-maps");
  return data;
}

export async function getConceptMap(id) {
  const { data } = await client.get(`/concept-maps/${id}`);
  return data;
}

export async function createConceptMap({ title, sourceText, sourceKind }) {
  const { data } = await client.post("/concept-maps", {
    title,
    source_text: sourceText,
    source_kind: sourceKind,
  });
  return data;
}

export async function deleteConceptMap(id) {
  await client.delete(`/concept-maps/${id}`);
}

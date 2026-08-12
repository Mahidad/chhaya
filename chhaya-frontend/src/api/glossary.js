import client from "./client";

/*
  Module 2 (Lamia): Word Lookup & Personal Glossary. lookupWord() hits the
  zero-API-call local dictionary endpoint; everything else is plain CRUD
  against a chapter's saved glossary entries.
*/

export async function lookupWord(word, topic) {
  const { data } = await client.get(`/dictionary/${encodeURIComponent(word)}`, {
    params: topic ? { topic } : {},
  });
  return data;
}

export async function listGlossary(chapterId) {
  const { data } = await client.get("/glossary", { params: { chapter_id: chapterId } });
  return data;
}

export async function saveGlossaryEntry({ chapterId, term, definition, partOfSpeech, source }) {
  const { data } = await client.post("/glossary", {
    chapter_id: chapterId,
    term,
    definition,
    part_of_speech: partOfSpeech || null,
    source: source || "wordnet",
  });
  return data;
}

export async function updateGlossaryEntry(entryId, definition) {
  const { data } = await client.patch(`/glossary/${entryId}`, { definition });
  return data;
}

export async function deleteGlossaryEntry(entryId) {
  await client.delete(`/glossary/${entryId}`);
}

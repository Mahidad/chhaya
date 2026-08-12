import client from "./client";

/*
  Module 2 (Lamia): Highlights.
*/

export async function listHighlights(contentType, contentId) {
  const { data } = await client.get("/highlights", {
    params: { content_type: contentType, content_id: contentId },
  });
  return data;
}

export async function createHighlight({ chapterId, contentType, contentId, quotedText, color }) {
  const { data } = await client.post("/highlights", {
    chapter_id: chapterId,
    content_type: contentType,
    content_id: contentId,
    quoted_text: quotedText,
    color: color || "amber",
  });
  return data;
}

export async function deleteHighlight(highlightId) {
  await client.delete(`/highlights/${highlightId}`);
}

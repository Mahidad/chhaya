import client from "./client";

/*
  Module 3 (Lamia): AI Voice Narration (Edge TTS). getNarrationAudioBlob
  follows the exact same blob-fetch pattern as getNoteFileBlob() in
  api/notes.js -- the browser's <audio> tag can't attach an Authorization
  header itself, so the file has to be fetched through axios (which does
  attach it, see api/client.js's interceptor) and turned into a local
  blob: URL instead of pointing <audio src> straight at the backend URL.
*/

export async function listVoices() {
  const { data } = await client.get("/voices");
  return data;
}

export async function listNarrations(contentType, contentId) {
  const { data } = await client.get("/narrations", {
    params: { content_type: contentType, content_id: contentId },
  });
  return data;
}

export async function createNarration({ contentType, contentId, teacherProfileId }) {
  const { data } = await client.post("/narrations", {
    content_type: contentType,
    content_id: contentId,
    teacher_profile_id: teacherProfileId || null,
  });
  return data;
}

export async function getNarration(narrationId) {
  const { data } = await client.get(`/narrations/${narrationId}`);
  return data;
}

export async function deleteNarration(narrationId) {
  await client.delete(`/narrations/${narrationId}`);
}

export async function getNarrationAudioBlob(narrationId) {
  const response = await client.get(`/narrations/${narrationId}/audio`, { responseType: "blob" });
  return response.data;
}

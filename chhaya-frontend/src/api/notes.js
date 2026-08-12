import client from "./client";

/*
  Module 2 (Lamia): Import / Upload Personal Notes. `createNote` follows
  the exact multipart/form-data pattern as uploadExamPaper() in
  api/examPapers.js -- text notes go through the same FormData shape as
  image/pdf notes so one backend endpoint can handle all three, see the
  comment in app/api/v1/endpoints/notes.py.
*/

export async function listNotes(chapterId) {
  const { data } = await client.get("/notes", { params: { chapter_id: chapterId } });
  return data;
}

export async function createNote({ chapterId, title, noteType, textContent, file }) {
  const formData = new FormData();
  formData.append("chapter_id", chapterId);
  formData.append("title", title);
  formData.append("note_type", noteType);
  if (textContent != null) formData.append("text_content", textContent);
  if (file) formData.append("file", file);

  const { data } = await client.post("/notes", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getNote(noteId) {
  const { data } = await client.get(`/notes/${noteId}`);
  return data;
}

export async function updateNote(noteId, { title, textContent } = {}) {
  const { data } = await client.patch(`/notes/${noteId}`, {
    title: title ?? null,
    text_content: textContent ?? null,
  });
  return data;
}

export async function deleteNote(noteId) {
  await client.delete(`/notes/${noteId}`);
}

export async function getNoteFileBlob(noteId) {
  const response = await client.get(`/notes/${noteId}/file`, { responseType: "blob" });
  return response.data;
}

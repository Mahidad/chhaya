import client from "./client";

/*
  Module 2 (Lamia): Course/Chapter organization. One function per backend
  route in app/api/v1/endpoints/courses.py, same shape as every other file
  in this folder (referenceSources.js, studyGuides.js, ...).
*/

// ---- Courses ----

export async function listCourses() {
  const { data } = await client.get("/courses");
  return data;
}

export async function createCourse(title) {
  const { data } = await client.post("/courses", { title });
  return data;
}

export async function getCourse(courseId) {
  const { data } = await client.get(`/courses/${courseId}`);
  return data;
}

export async function renameCourse(courseId, title) {
  const { data } = await client.patch(`/courses/${courseId}`, { title });
  return data;
}

export async function deleteCourse(courseId) {
  await client.delete(`/courses/${courseId}`);
}

export async function reorderCourses(orderedIds) {
  const { data } = await client.patch("/courses/reorder", { ordered_ids: orderedIds });
  return data;
}

// ---- Chapters ----

export async function listChapters(courseId) {
  const { data } = await client.get(`/courses/${courseId}/chapters`);
  return data;
}

export async function createChapter(courseId, title) {
  const { data } = await client.post(`/courses/${courseId}/chapters`, { title });
  return data;
}

export async function getChapter(chapterId) {
  const { data } = await client.get(`/chapters/${chapterId}`);
  return data;
}

export async function renameChapter(chapterId, title) {
  const { data } = await client.patch(`/chapters/${chapterId}`, { title });
  return data;
}

export async function deleteChapter(chapterId) {
  await client.delete(`/chapters/${chapterId}`);
}

export async function reorderChapters(courseId, orderedIds) {
  const { data } = await client.patch(`/courses/${courseId}/chapters/reorder`, {
    ordered_ids: orderedIds,
  });
  return data;
}

// The Chapter Workspace page's one-call load: chapter + everything filed
// inside it, instead of three separate round trips.
export async function getChapterContents(chapterId) {
  const { data } = await client.get(`/chapters/${chapterId}/contents`);
  return data;
}

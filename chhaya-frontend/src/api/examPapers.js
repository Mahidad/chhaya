import client from "./client";

export async function listExamPapers() {
  const { data } = await client.get("/exam-papers");
  return data;
}

export async function getExamPaper(id) {
  const { data } = await client.get(`/exam-papers/${id}`);
  return data;
}

export async function uploadExamPaper({ title, course, file }) {
  // multipart/form-data, not JSON -- has to match the backend's Form(...)/File(...)
  // fields exactly. See the comment in app/api/v1/endpoints/exam_papers.py for why
  // this endpoint can't just take a Pydantic body like the others.
  const formData = new FormData();
  formData.append("title", title);
  if (course) formData.append("course", course);
  formData.append("file", file);

  const { data } = await client.post("/exam-papers", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteExamPaper(id) {
  await client.delete(`/exam-papers/${id}`);
}


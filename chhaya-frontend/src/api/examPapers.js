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

export async function getExamPaperFileBlob(id) {
  const response = await client.get(`/exam-papers/${id}/file`, {
    responseType: "blob",     // binary large object
  });
  return response.data;    // pdf data will be in the form of blob
}



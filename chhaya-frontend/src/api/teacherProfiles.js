import client from "./client";

export async function listTeacherProfiles() {
  const { data } = await client.get("/teacher-profiles");
  return data;
}

export async function updateTeacherProfile(id, changes) {
  // `changes` is a partial object, e.g. { is_favorite: true } or { display_name: "New name" }.
  // Matches the backend's PATCH semantics -- see the comment in
  // app/api/v1/endpoints/teacher_profiles.py for why one endpoint covers both.
  const { data } = await client.patch(`/teacher-profiles/${id}`, changes);
  return data;
}

export async function deleteTeacherProfile(id) {
  await client.delete(`/teacher-profiles/${id}`);
}

export async function getPreferenceProfile() {
  const { data } = await client.get("/teacher-profiles/preference");
  return data;
}

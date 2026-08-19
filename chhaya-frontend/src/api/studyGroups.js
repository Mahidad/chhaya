import client from "./client";

export async function listStudyGroups() {
  const { data } = await client.get("/study-groups");
  return data;
}

export async function getStudyGroup(id) {
  const { data } = await client.get(`/study-groups/${id}`);
  return data;
}

export async function deleteStudyGroup(id) {
  await client.delete(`/study-groups/${id}`);
}

export async function createStudyGroup({ name, description }) {
  const { data } = await client.post("/study-groups", { name, description });
  return data;
}

export async function requestToJoin(id) {
  await client.post(`/study-groups/${id}/join-request`);
}

export async function inviteStudent(id, email) {
  await client.post(`/study-groups/${id}/invite`, { email });
}

export async function getInvitations() {
  const { data } = await client.get("/study-groups/invitations");
  return data;
}

export async function respondToInvitation(id, status) {
  await client.post(`/study-groups/invitations/${id}/respond`, { status });
}

export async function respondToJoinRequest(groupId, requestId, status) {
  await client.post(`/study-groups/${groupId}/join-requests/${requestId}/respond`, { status });
}

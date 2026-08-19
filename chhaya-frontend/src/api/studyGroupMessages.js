import client from "./client";

export async function listGroupMessages(groupId) {
  const { data } = await client.get(`/study-groups/${groupId}/messages`);
  return data;
}

export async function postGroupMessage(groupId, content) {
  const { data } = await client.post(`/study-groups/${groupId}/messages`, { content });
  return data;
}

export async function setMessagePin(groupId, messageId, pinned) {
  const action = pinned ? "pin" : "unpin";
  await client.post(`/study-groups/${groupId}/messages/${messageId}/${action}`);
}

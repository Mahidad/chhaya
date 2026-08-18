import client from "./client";

export async function listCodeWorkspaceFolders() {
  const { data } = await client.get("/code-workspace-folders");
  return data;
}

export async function createCodeWorkspaceFolder(name) {
  const { data } = await client.post("/code-workspace-folders", { name });
  return data;
}

export async function renameCodeWorkspaceFolder(id, name) {
  const { data } = await client.patch(`/code-workspace-folders/${id}`, { name });
  return data;
}

export async function deleteCodeWorkspaceFolder(id) {
  // Backend un-files the folder's contents (sets folder_id back to null)
  // before deleting the folder itself -- nothing inside it is lost.
  await client.delete(`/code-workspace-folders/${id}`);
}

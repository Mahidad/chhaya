import client from "./client";

/*
  One function per endpoint, named after what it does rather than the HTTP
  verb+path. Pages call `listReferenceSources()`, not
  `client.get('/reference-sources')` -- if the URL ever changes, this is
  the only file that needs to know.
*/

export async function listReferenceSources() {
  const { data } = await client.get("/reference-sources");
  return data;
}

export async function getReferenceSource(id) {
  const { data } = await client.get(`/reference-sources/${id}`);
  return data;
}

export async function createReferenceSource({ title, sourceType, url }) {
  const { data } = await client.post("/reference-sources", {
    title,
    source_type: sourceType,
    url,
  });
  return data;
}

export async function deleteReferenceSource(id) {
  await client.delete(`/reference-sources/${id}`);
}

export async function getSourceProfile(id) {
  const { data } = await client.get(`/reference-sources/${id}/profile`);
  return data;
}

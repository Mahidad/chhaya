import client from "./client";

export async function findNarration({ noteId, studyGuideId }) {
  // Returns null when nothing has been generated yet -- lets a page show
  // a "Generate narration" button instead of a player, without kicking
  // off generation just by loading.
  const { data } = await client.get("/voice-narrations", {
    params: noteId ? { note_id: noteId } : { study_guide_id: studyGuideId },
  });
  return data;
}

export async function generateNarration({ noteId, studyGuideId, teacherProfileId, regenerate = false }) {
  // teacherProfileId only applies to notes -- a study guide's narration
  // inherits the teacher style the guide was already written in, and the
  // backend rejects the combination outright.
  const { data } = await client.post(
    "/voice-narrations",
    {
      note_id: noteId || null,
      study_guide_id: studyGuideId || null,
      teacher_profile_id: teacherProfileId || null,
    },
    { params: { regenerate } }
  );
  return data;
}

export function narrationAudioUrl(narrationId) {
  // Built from the same base URL the axios client uses so it works in
  // dev and deployed alike.
  const base = client.defaults.baseURL || "";
  return `${base}/voice-narrations/${narrationId}/audio`;
}

export async function deleteNarration(id) {
  await client.delete(`/voice-narrations/${id}`);
}

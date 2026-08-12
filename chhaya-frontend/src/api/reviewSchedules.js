/** Frontend API helpers for Amiyo's Module 2 spaced-repetition feature. */

import client from "./client";


export async function listReviews(status = "all") {
  const { data } = await client.get("/reviews", { params: { status } });
  return data;
}


export async function addGuideToSchedule(studyGuideId) {
  await client.post(`/reviews/study-guides/${studyGuideId}`);
}


export async function rateReview(reviewId, quality) {
  const { data } = await client.put(`/reviews/${reviewId}/rate`, { quality });
  return data;
}


export async function deleteReview(reviewId) {
  await client.delete(`/reviews/${reviewId}`);
}


export async function checkReviewReminders() {
  const { data } = await client.post("/reviews/reminders/check");
  return data;
}

import { useEffect, useState } from "react";

import AppShell from "../../components/layout/AppShell";
import Button from "../../components/ui/Button";
import Icon from "../../components/icons/Icon";
import {
  deleteReview,
  listReviews,
  rateReview,
} from "../../api/reviewSchedules";


const FILTERS = [
  { value: "due", label: "Due now" },
  { value: "upcoming", label: "Upcoming" },
  { value: "all", label: "All reviews" },
];

const RATINGS = [
  { label: "Again", quality: 0, variant: "danger" },
  { label: "Hard", quality: 2, variant: "ghost" },
  { label: "Good", quality: 4, variant: "primary" },
  { label: "Easy", quality: 5, variant: "quiet" },
];


function formatDate(value) {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}


export default function ReviewSchedulePage() {
  const [filter, setFilter] = useState("due");
  const [reviews, setReviews] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function loadReviews(selectedFilter = filter) {
    setError("");
    try {
      const data = await listReviews(selectedFilter);
      setReviews(data);
    } catch {
      setError("Could not load your review schedule. Is the backend running?");
    }
  }

  useEffect(() => {
    loadReviews();
  }, []);

  async function changeFilter(nextFilter) {
    setFilter(nextFilter);
    setReviews(null);
    await loadReviews(nextFilter);
  }

  async function handleRating(reviewId, quality) {
    setBusyId(reviewId);
    try {
      await rateReview(reviewId, quality);
      await loadReviews();
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(reviewId) {
    if (!window.confirm("Remove this topic from your review schedule?")) return;
    setBusyId(reviewId);
    try {
      await deleteReview(reviewId);
      await loadReviews();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell section="Learning" current="Review schedule">
      <div className="page-head">
        <div>
          <div className="page-title">Review schedule</div>
          <div className="page-sub">
            Add a completed guide from Study guides, then rate each review here.
          </div>
        </div>
      </div>

      <div className="tab-bar">
        {FILTERS.map((item) => (
          <button
            key={item.value}
            className={`tab-btn ${filter === item.value ? "tab-btn-on" : ""}`}
            onClick={() => changeFilter(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {error && <div className="banner banner-danger">{error}</div>}

      {reviews === null ? (
        <div className="card card-pad" style={{ color: "var(--muted)" }}>Loading reviews...</div>
      ) : reviews.length === 0 ? (
        <div className="card card-pad" style={{ color: "var(--muted)" }}>
          No {filter === "due" ? "reviews due today" : "reviews in this list"}. Add a completed guide from Study guides to schedule it.
        </div>
      ) : (
        <div className="list-card">
          {reviews.map((review) => (
            <div className="prow" key={review.id} style={{ display: "block" }}>
              <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ flex: "1 1 230px" }}>
                  <div style={{ fontWeight: 700, color: "var(--ink)" }}>{review.topic}</div>
                  <div className="hint" style={{ marginTop: 4 }}>
                    {review.next_review_date < new Date().toISOString().slice(0, 10) ? "Overdue" : "Due"} {formatDate(review.next_review_date)}
                    {" · "}interval {review.interval_days || 1} day{review.interval_days === 1 ? "" : "s"}
                    {" · "}ease {review.ease_factor.toFixed(2)}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={busyId === review.id}
                  onClick={() => handleDelete(review.id)}
                  icon={<Icon name="trash" size={14} />}
                >
                  Remove
                </Button>
              </div>

              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 14 }}>
                <span className="hint" style={{ alignSelf: "center", marginRight: 2 }}>How well did you recall it?</span>
                {RATINGS.map((rating) => (
                  <Button
                    key={rating.label}
                    variant={rating.variant}
                    size="sm"
                    disabled={busyId === review.id}
                    onClick={() => handleRating(review.id, rating.quality)}
                  >
                    {rating.label}
                  </Button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </AppShell>
  );
}

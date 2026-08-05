/**
 * SessionTracker.jsx
 * Amiyo – Module 1 Feature 4: Analytics Dashboard
 *
 * What is a "study session"?
 * --------------------------
 * A session = one continuous login visit to the Chhaya app.
 * It starts once when the user logs in and the app loads.
 * It ends when they close the tab or the browser unloads the page.
 * Duration is measured in seconds.
 *
 * Why sessionStorage guard?
 * -------------------------
 * React's <StrictMode> in development double-invokes useEffect (mount →
 * unmount → mount again) to catch side effects. Without a guard, this
 * creates two DB rows per login. The guard stores the active session ID
 * in sessionStorage so the second mount finds it and skips the API call.
 * sessionStorage is cleared when the tab closes, so each new tab/login
 * correctly starts a fresh session.
 *
 * Why is this component at the top of App.jsx (outside route tree)?
 * -----------------------------------------------------------------
 * Placing it inside a single route (e.g. "/") caused it to re-mount
 * every time the user navigated back to that page, creating a new session
 * on every tab switch. Mounting it once at the app root means one session
 * per login, regardless of which pages the student visits.
 *
 * Token handling
 * --------------
 * Native fetch() with keepalive:true is used for the end-session call —
 * axios doesn't support keepalive, and we need it to fire even when the
 * browser tab is closing.
 */

import { useEffect, useRef } from "react";
import { startStudySession } from "../api/progress";
import { useAuth } from "../context/AuthContext";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const SESSION_KEY = "chhaya_active_session_id";
const SESSION_START_KEY = "chhaya_session_start_ms";

export default function SessionTracker() {
  const { user } = useAuth();
  const sessionIdRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    // Do not create a session until authentication is complete. This also
    // starts tracking immediately after an in-app login, without a reload.
    if (!user) return undefined;

    // ── Guard: skip if a session is already tracked in this tab ───────────
    // This prevents React StrictMode's double-mount from creating two rows.
    const existingId = sessionStorage.getItem(SESSION_KEY);
    const existingStart = sessionStorage.getItem(SESSION_START_KEY);
    if (existingId && existingStart) {
      sessionIdRef.current = existingId;
      startTimeRef.current = parseInt(existingStart, 10);
      // Session already started — just re-attach the beforeunload handler
      window.addEventListener("beforeunload", handleUnload);
      return () => window.removeEventListener("beforeunload", handleUnload);
    }

    // ── Start a new session ────────────────────────────────────────────────
    startStudySession()
      .then((session) => {
        sessionIdRef.current = session.id;
        startTimeRef.current = Date.now();
        // Persist to sessionStorage so StrictMode's second mount finds it
        sessionStorage.setItem(SESSION_KEY, session.id);
        sessionStorage.setItem(SESSION_START_KEY, String(Date.now()));
        window.dispatchEvent(new Event("chhaya-session-started"));
      })
      .catch(() => {
        // Never let a tracking failure break the UI
      });

    // ── End session on tab/browser close ──────────────────────────────────
    function handleUnload() {
      const sessionId = sessionIdRef.current;
      const startTime = startTimeRef.current;
      if (!sessionId || !startTime) return;

      const durationSecs = Math.round((Date.now() - startTime) / 1000);
      if (durationSecs < 5) return; // ignore accidental sub-5-second visits

      const token = localStorage.getItem("chhaya_token");
      if (!token) return;

      // keepalive: true fires even while the page is unloading
      fetch(`${API_BASE}/progress/study-sessions/${sessionId}/end`, {
        method: "PUT",
        keepalive: true,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ duration_secs: durationSecs }),
      }).catch(() => {});

      // Clear sessionStorage so the next tab/login starts fresh
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(SESSION_START_KEY);
    }

    window.addEventListener("beforeunload", handleUnload);

    return () => {
      window.removeEventListener("beforeunload", handleUnload);
      // On logout (component unmounts before tab closes), end the session
      handleUnload();
    };
  }, [user]);

  return null;
}

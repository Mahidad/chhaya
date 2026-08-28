/**
 * SessionTracker.jsx
 * Amiyo – Module 1 Feature 4: Analytics Dashboard
 *
 * What is a "study session"?
 * --------------------------
 * A session = one continuous login visit to the Chhaya app.
 * It starts once when the user logs in and the app loads.
 * It ends when they close the tab, navigate away, or the browser unloads
 * the page. Simply switching to another tab or minimizing the window does
 * NOT end the session — the timer keeps running until the tab is actually
 * closed or navigated away from. Duration is measured in seconds.
 *
 * Why sessionStorage guard?
 * -------------------------
 * React's <StrictMode> double-invokes useEffect (mount → unmount → mount)
 * to catch side effects. Without a guard, this creates two DB rows per login.
 * The guard stores the active session ID in sessionStorage so the second
 * mount finds it and skips the API call. sessionStorage is cleared when the
 * tab closes, so each new tab/login correctly starts a fresh session.
 *
 * Why pagehide in addition to beforeunload?
 * -----------------------------------------
 * Modern browsers do not reliably fire beforeunload on every tab-close path
 * (bfcache handling can kill the page before the fetch completes). pagehide
 * fires on real tab close and navigation without firing on ordinary
 * tab-switch/minimize, so it's the better close signal. Both are registered
 * and a guard prevents double-firing.
 *
 * Why a heartbeat?
 * ----------------
 * Even pagehide + beforeunload can be silently dropped by the browser in
 * certain scenarios (mobile Safari, Vercel deployments behind bfcache, etc.).
 * A 60-second heartbeat writes the current duration to the DB periodically.
 * This means even if the close handler never fires, the session will have
 * been updated within the last 60 seconds — avoiding the "study time resets
 * to 0 on every visit" problem that would occur when duration_secs = null.
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
const HEARTBEAT_LAST_KEY = "chhaya_last_heartbeat_ms"; // updated after each heartbeat save
const HEARTBEAT_INTERVAL_MS = 60_000; // save duration every 60 seconds

export default function SessionTracker() {
  const { user } = useAuth();
  const sessionIdRef = useRef(null);
  const startTimeRef = useRef(null);
  const endedRef = useRef(false); // guards against double-firing (beforeunload + pagehide)

  useEffect(() => {
    if (!user) return undefined;

    // ── Shared helper: send duration to the backend ────────────────────────
    // Used by both the heartbeat and the close handler.
    // keepalive: true allows the fetch to outlive the page when unloading.
    function sendDuration({ keepalive = false } = {}) {
      const sessionId = sessionIdRef.current;
      const startTime = startTimeRef.current;
      if (!sessionId || !startTime) return;

      const durationSecs = Math.round((Date.now() - startTime) / 1000);
      if (durationSecs < 5) return; // ignore accidental sub-5-second visits

      const token = localStorage.getItem("chhaya_token");
      if (!token) return;

      fetch(`${API_BASE}/progress/study-sessions/${sessionId}/end`, {
        method: "PUT",
        keepalive,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ duration_secs: durationSecs }),
      }).catch(() => { });
    }

    // ── End session on tab close / navigation away ─────────────────────────
    function handleUnload() {
      if (endedRef.current) return; // already ended by the other handler
      endedRef.current = true;

      sendDuration({ keepalive: true });

      // Clear sessionStorage so the next tab/login starts fresh
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(SESSION_START_KEY);
      sessionStorage.removeItem(HEARTBEAT_LAST_KEY);
    }

    // ── Heartbeat: save duration every 60 seconds ──────────────────────────
    // Protects against close-handler failures on Vercel / mobile / bfcache.
    // After each save, update HEARTBEAT_LAST_KEY so the dashboard knows how
    // much time is already persisted and avoids double-counting.
    const heartbeat = setInterval(() => {
      sendDuration({ keepalive: false });
      sessionStorage.setItem(HEARTBEAT_LAST_KEY, String(Date.now()));
    }, HEARTBEAT_INTERVAL_MS);

    // ── Guard: skip creating a new session if one is already tracked ───────
    // This prevents React StrictMode's double-mount from creating two rows.
    const existingId = sessionStorage.getItem(SESSION_KEY);
    const existingStart = sessionStorage.getItem(SESSION_START_KEY);
    if (existingId && existingStart) {
      sessionIdRef.current = existingId;
      startTimeRef.current = parseInt(existingStart, 10);
      endedRef.current = false;
      window.addEventListener("beforeunload", handleUnload);
      window.addEventListener("pagehide", handleUnload);
      return () => {
        clearInterval(heartbeat);
        window.removeEventListener("beforeunload", handleUnload);
        window.removeEventListener("pagehide", handleUnload);
      };
    }

    // ── Start a new session ────────────────────────────────────────────────
    startStudySession()
      .then((session) => {
        sessionIdRef.current = session.id;
        startTimeRef.current = Date.now();
        endedRef.current = false;
        // Persist to sessionStorage so StrictMode's second mount finds it
        sessionStorage.setItem(SESSION_KEY, session.id);
        sessionStorage.setItem(SESSION_START_KEY, String(Date.now()));
        window.dispatchEvent(new Event("chhaya-session-started"));
      })
      .catch(() => {
        // Never let a tracking failure break the UI
      });

    window.addEventListener("beforeunload", handleUnload);
    window.addEventListener("pagehide", handleUnload);

    return () => {
      clearInterval(heartbeat);
      window.removeEventListener("beforeunload", handleUnload);
      window.removeEventListener("pagehide", handleUnload);
      // On logout (component unmounts before tab closes), end the session
      handleUnload();
    };
  }, [user]);

  return null;
}

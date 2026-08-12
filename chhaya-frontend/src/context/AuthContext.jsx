import { createContext, useContext, useState, useCallback, useEffect } from "react";
import * as authApi from "../api/auth";

/*
  Holds "who's logged in" in one place so any component can ask via
  `useAuth()` instead of prop-drilling `user` through every layout and
  page. The token itself lives in localStorage (survives a page refresh);
  this context mirrors it into React state so components re-render when
  login/logout happens.
*/

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("chhaya_user");
    const loginDate = localStorage.getItem("chhaya_login_date");
    if (saved && loginDate === getLocalDateKey()) return JSON.parse(saved);

    // Old sessions and sessions from a previous calendar day must log in again.
    localStorage.removeItem("chhaya_token");
    localStorage.removeItem("chhaya_user");
    localStorage.removeItem("chhaya_login_date");
    return null;
  });
  const [loading, setLoading] = useState(false);

  const logout = useCallback(() => {
    localStorage.removeItem("chhaya_token");
    localStorage.removeItem("chhaya_user");
    localStorage.removeItem("chhaya_login_date");
    setUser(null);
  }, []);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    try {
      const { access_token } = await authApi.login({ email, password });
      localStorage.setItem("chhaya_token", access_token);
      const me = await authApi.fetchMe();
      localStorage.setItem("chhaya_user", JSON.stringify(me));
      localStorage.setItem("chhaya_login_date", getLocalDateKey());
      setUser(me);
      // A reminder failure must never block a successful login.
      checkReviewReminders().catch(() => { });
      return me;
    } finally {
      setLoading(false);
    }
  }, []);

  const signup = useCallback(async (fullName, email, password) => {
    setLoading(true);
    try {
      await authApi.signup({ fullName, email, password });
      return login(email, password);
    } finally {
      setLoading(false);
    }
  }, [login]);

  useEffect(() => {
    if (!user) return undefined;

    function logoutIfDayChanged() {
      if (localStorage.getItem("chhaya_login_date") !== getLocalDateKey()) {
        logout();
      }
    }

    // Also check when a background tab becomes visible again after midnight.
    window.addEventListener("visibilitychange", logoutIfDayChanged);
    const timer = window.setInterval(logoutIfDayChanged, 60_000);
    return () => {
      window.removeEventListener("visibilitychange", logoutIfDayChanged);
      window.clearInterval(timer);
    };
  }, [user, logout]);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

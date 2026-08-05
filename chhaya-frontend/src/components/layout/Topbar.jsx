import { useState } from "react";
import Icon from "../icons/Icon";
import { useAuth } from "../../context/AuthContext";
import { useLanguage } from "../../context/LanguageContext";

function initials(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return (parts[0][0] + (parts[1]?.[0] || "")).toUpperCase();
}

export default function Topbar({ section, current }) {
  const { user, logout } = useAuth();
  const { lang, setLang, t } = useLanguage();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="topbar">
      <div className="crumbs">
        <span>{section}</span>
        <Icon name="chevronRight" size={14} />
        <span className="crumb-now">{current}</span>
      </div>
      <div className="topbar-right">
        <div className="searchbar">
          <Icon name="search" size={16} />
          <span>{t("searchPlaceholder")}</span>
        </div>
        <div className="lang-toggle">
          <button
            className={`lang-option ${lang === "en" ? "active" : ""}`}
            onClick={() => setLang("en")}
          >
            EN
          </button>
          <button
            className={`lang-option bn ${lang === "bn" ? "active" : ""}`}
            onClick={() => setLang("bn")}
          >
            বাংলা
          </button>
        </div>
        <div className="icon-btn">
          <Icon name="bell" size={16} />
        </div>
        <div style={{ position: "relative" }}>
          <div className="avatar" style={{ cursor: "pointer" }} onClick={() => setMenuOpen((v) => !v)}>
            {initials(user?.full_name)}
          </div>
          {menuOpen && (
            <div
              className="card"
              style={{ position: "absolute", right: 0, top: 44, width: 180, zIndex: 10 }}
            >
              <div className="card-pad" style={{ padding: 12 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{user?.full_name}</div>
                <div style={{ fontSize: 11, color: "var(--faint)", marginTop: 2 }}>{user?.email}</div>
                <button
                  className="btn btn-ghost btn-sm"
                  style={{ width: "100%", marginTop: 10, justifyContent: "center" }}
                  onClick={logout}
                >
                  <Icon name="logout" size={14} /> Log out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

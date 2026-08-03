import { NavLink } from "react-router-dom";
import Icon from "../icons/Icon";
import logoBlack from "../../assets/logo-black.png";

/*
  The mark's background changed from
  solid green to white specifically so the logo's black
  linework stays visible against it -- black-on-green would have nearly
  disappeared at 32px. See the frontend notes in the handoff message for
  the couple of other spots (favicon, auth screen) using the white
  transparent variant instead, for the dark sidebar/hero backgrounds.
*/

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: "overview" },
  { to: "/sources", label: "Reference sources", icon: "sources" },
  { to: "/library", label: "Style library", icon: "library" },
  { to: "/guides", label: "Study guides", icon: "guides" },
  { to: "/concept-maps", label: "Concept maps", icon: "conceptMap" },
  { to: "/exam-papers", label: "Upload questions", icon: "exams" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <img src={logoBlack} alt="Chhaya" />
        </div>
        <div>
          <div className="brand-name">Chhaya</div>
          <div className="brand-sub bn">ছায়া</div>
        </div>
      </div>

      <nav className="nav">
        <div className="nav-label">Learn</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            <Icon name={item.icon} size={18} strokeWidth="1.6" />
            <span>{item.label}</span>
            <span className="nav-dot" />
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div className="plan-card">
          <div className="plan-title">Style credits</div>
          <div className="plan-meta">6 of 10 used this month</div>
          <div className="plan-bar">
            <div className="plan-bar-fill" style={{ width: "60%" }} />
          </div>
        </div>
        <NavLink to="/settings" className="nav-item" style={{ marginTop: 8 }}>
          <Icon name="settings" size={18} />
          <span>Settings</span>
          <span className="nav-dot" />
        </NavLink>
      </div>
    </aside>
  );
}

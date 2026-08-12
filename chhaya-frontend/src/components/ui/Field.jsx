import { useState } from "react";
import Icon from "../icons/Icon";

/*
  The mockup's `.input` div was static (just showing example text). These
  wrap a real <input>/<select> in the same `.input`/`.select` box styling
  so the visual is identical but the field is actually editable and
  controlled by React state -- the difference between a picture of a form
  and a form.
*/

export function TextField({ label, hint, icon, ...inputProps }) {
  return (
    <div className="field">
      {label && <div className="label">{label}</div>}
      <div className="input">
        {icon && <Icon name={icon} size={16} />}
        <input
          {...inputProps}
          style={{ border: "none", outline: "none", background: "transparent", flex: 1, height: "100%" }}
        />
      </div>
      {hint && <div className="hint">{hint}</div>}
    </div>
  );
}

/*
  Mirrors app/schemas/user.py's PASSWORD_REQUIREMENTS exactly -- same
  labels, same order, same rules. If the backend's rules ever change,
  update both places; keeping them in the same shape (label + test
  function) makes it obvious when they've drifted apart, since a password
  the UI shows as "all green" getting rejected by the API is a bad
  experience for exactly one reason: these two lists disagreeing.
*/
export const PASSWORD_REQUIREMENTS = [
  { label: "At least 8 characters", test: (pw) => pw.length >= 8 },
  { label: "One uppercase letter", test: (pw) => /[A-Z]/.test(pw) },
  { label: "One lowercase letter", test: (pw) => /[a-z]/.test(pw) },
  { label: "One number", test: (pw) => /\d/.test(pw) },
  { label: "One special character (!@#$...)", test: (pw) => /[^A-Za-z0-9]/.test(pw) },
];

/*
  `showStrength`: pass true on the signup form (where a student is
  choosing a new password and benefits from live feedback) and leave it
  false on login (where re-showing "requirements" for an existing
  password is just noise -- they already have one).
*/
export function PasswordField({ label, hint, showStrength = false, value = "", ...inputProps }) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="field">
      {label && <div className="label">{label}</div>}
      <div className="input">
        <input
          {...inputProps}
          value={value}
          type={visible ? "text" : "password"}
          style={{ border: "none", outline: "none", background: "transparent", flex: 1, height: "100%" }}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--faint)", display: "flex" }}
        >
          <Icon name={visible ? "eyeOff" : "eye"} size={16} />
        </button>
      </div>
      {hint && <div className="hint">{hint}</div>}
      {showStrength && value && (
        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 4 }}>
          {PASSWORD_REQUIREMENTS.map((req) => {
            const passed = req.test(value);
            return (
              <div key={req.label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11 }}>
                {passed ? (
                  <Icon name="check" size={11} style={{ color: "var(--ok)" }} />
                ) : (
                  <span style={{ width: 11, textAlign: "center", color: "var(--faint)" }}>•</span>
                )}
                <span style={{ color: passed ? "var(--ok)" : "var(--faint)" }}>{req.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function SelectField({ label, hint, children, ...selectProps }) {
  return (
    <div className="field">
      {label && <div className="label">{label}</div>}
      <select className="select" {...selectProps}>
        {children}
      </select>
      {hint && <div className="hint">{hint}</div>}
    </div>
  );
}

export function Checkbox({ checked, onChange, label, sub, right }) {
  return (
    <div className="opt-row">
      <div className={`check ${checked ? "check-on" : ""}`} onClick={onChange} role="checkbox" aria-checked={checked}>
        {checked && <Icon name="check" size={12} strokeWidth="3" />}
      </div>
      <div>
        <div className="opt-text">{label}</div>
        {sub && <div className="opt-sub">{sub}</div>}
      </div>
      {right && <div className="opt-right">{right}</div>}
    </div>
  );
}

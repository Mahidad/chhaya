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

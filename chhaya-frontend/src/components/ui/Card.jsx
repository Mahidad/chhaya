export function Card({ children, className = "", style }) {
  return (
    <div className={`card ${className}`} style={style}>
      {children}
    </div>
  );
}

export function CardHead({ title, note }) {
  return (
    <div className="card-head">
      <span className="card-title">{title}</span>
      {note && <span className="card-note">{note}</span>}
    </div>
  );
}

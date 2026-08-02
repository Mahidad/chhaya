export default function Badge({ variant, children, icon = null, className = "" }) {
  const classes = ["badge", variant && `badge-${variant}`, className].filter(Boolean).join(" ");
  return (
    <span className={classes}>
      {icon}
      {children}
    </span>
  );
}

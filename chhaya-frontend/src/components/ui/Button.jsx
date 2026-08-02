/*
  Wraps the `.btn` classes from the design system. Using this component
  instead of raw `<button className="btn btn-primary">` everywhere means
  a later change (say, adding a loading spinner to every button at once)
  happens in one file.
*/
export default function Button({
  variant = "primary", // primary | ghost | quiet | danger
  size,                // undefined (default) | sm | lg
  icon = null,
  children,
  className = "",
  ...rest
}) {
  const classes = ["btn", `btn-${variant}`, size && `btn-${size}`, className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} {...rest}>
      {icon}
      {children}
    </button>
  );
}

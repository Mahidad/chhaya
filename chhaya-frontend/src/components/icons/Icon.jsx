/*
  Every icon in the Figma export is the same inline-SVG pattern with a
  different `<path>`. Rather than pasting that boilerplate 60+ times
  across the app, `PATHS` holds just the shape data, and `<Icon name="..." />`
  wraps it in one consistent `<svg>`. Add a new icon by adding one line to
  PATHS -- never touch the component itself.
*/

const PATHS = {
  overview: <path d="M3 10l9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z" />,
  sources: (
    <>
      <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
      <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
    </>
  ),
  library: (
    <>
      <path d="M12 3l9 5-9 5-9-5 9-5z" />
      <path d="M3 14l9 5 9-5" />
    </>
  ),
  guides: (
    <>
      <path d="M4 5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 1-2-2z" />
      <path d="M8 3v18" />
    </>
  ),
  conceptMap: (
    <>
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="10" r="2.5" />
      <circle cx="9" cy="18" r="2.5" />
      <path d="M8 7l8 2M8 16l8-4" />
    </>
  ),
  exams: (
    <>
      <path d="M5 3h14v18H5z" />
      <path d="M9 8h6M9 12h6M9 16h3" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1L7 17M17 7l2.1-2.1" />
    </>
  ),
  chevronRight: <path d="M9 6l6 6-6 6" />,
  chevronDown: <path d="M6 9l6 6 6-6" />,
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-3.5-3.5" />
    </>
  ),
  bell: (
    <>
      <path d="M18 8a6 6 0 1 0-12 0c0 7-2 8-2 8h16s-2-1-2-8" />
      <path d="M10 20a2 2 0 0 0 4 0" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  fileText: (
    <>
      <path d="M6 3h8l4 4v14H6z" />
      <path d="M14 3v4h4" />
      <path d="M9 12h6M9 16h6" />
    </>
  ),
  check: <path d="M4 12.5l5 5L20 6.5" />,
  refresh: (
    <>
      <path d="M20 6v5h-5" />
      <path d="M4 18v-5h5" />
      <path d="M19 11a7 7 0 0 0-12-3L4 11" />
      <path d="M5 13a7 7 0 0 0 12 3l3-3" />
    </>
  ),
  pin: <path d="M15 3l6 6-3 1-4 4-1 5-2-2-4 4-1-1 4-4-2-2 5-1 4-4z" />,
  alertTriangle: (
    <>
      <path d="M12 4l9 16H3z" />
      <path d="M12 10v4M12 17.5v.1" />
    </>
  ),
  logout: (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </>
  ),
  eye: (
    <>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  folder: (
    <path d="M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z" />
  ),
  code: (
    <>
      <path d="M9 8l-5 4 5 4" />
      <path d="M15 8l5 4-5 4" />
    </>
  ),
  wand: (
    <>
      <path d="M4 20l9-9" />
      <path d="M14.5 3.5l1 2 2 1-2 1-1 2-1-2-2-1 2-1z" />
      <path d="M18.5 9.5l.6 1.2 1.2.6-1.2.6-.6 1.2-.6-1.2-1.2-.6 1.2-.6z" />
    </>
  ),
  swap: (
    <>
      <path d="M7 4l0 13" />
      <path d="M4 14l3 3 3-3" />
      <path d="M17 20l0-13" />
      <path d="M20 10l-3-3-3 3" />
    </>
  ),
  eyeOff: (
    <>
      <path d="M3 3l18 18" />
      <path d="M10.6 5.1A10.7 10.7 0 0 1 12 5c6.5 0 10 7 10 7a17.6 17.6 0 0 1-3.2 4.1M6.5 6.6C3.7 8.4 2 12 2 12s3.5 7 10 7a10.4 10.4 0 0 0 4.2-.9" />
      <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
    </>
  ),
  trash: (
    <>
      <path d="M4 7h16" />
      <path d="M10 11v6M14 11v6" />
      <path d="M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13" />
      <path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3" />
    </>
  ),
  courses: (
    <>
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </>
  ),
};

export default function Icon({ name, size = 16, className = "", ...rest }) {
  const path = PATHS[name];
  if (!path) return null;
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...rest}
    >
      {path}
    </svg>
  );
}

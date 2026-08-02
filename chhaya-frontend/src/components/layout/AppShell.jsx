import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

/*
  Every logged-in page is: sidebar + topbar + content. Pages just pass
  what the breadcrumb should say and drop their content as children --
  they never rebuild the shell themselves. That's what makes it trivial
  for Lamia/Omar/Amiyo's screens to look consistent with Mahidad's: reuse
  this, don't reinvent it.
*/
export default function AppShell({ section, current, flush = false, children }) {
  return (
    <div className="app">
      <Sidebar />
      <div className="main">
        <Topbar section={section} current={current} />
        <div className={flush ? "content-flush" : "content"}>{children}</div>
      </div>
    </div>
  );
}

import AppShell from "../components/layout/AppShell";

/*
  Placeholder for the other three members' modules (style library, study
  guides, concept maps, mock exams) so the sidebar nav doesn't 404 while
  this is the only module built out. Delete this file's usage for a route
  once that module gets its own real page -- see the backend README's
  "Adding a new module" section for the matching backend steps.
*/
export default function ComingSoonPage({ title }) {
  return (
    <AppShell section={title} current="Coming soon">
      <div className="page-head">
        <div>
          <div className="page-title">{title}</div>
          <div className="page-sub">This module hasn't been built yet.</div>
        </div>
      </div>
    </AppShell>
  );
}

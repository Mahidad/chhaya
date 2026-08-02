# Chhaya Frontend

React (Vite) app converted from the Figma export, kept deliberately simple
since the team is new to React. No Redux, no TanStack Query, no CSS
framework — just `useState`/`useEffect`/Context and the same class-based
CSS the mockups already used.

## Setup

```bash
npm install
cp .env.example .env       # points at the backend, defaults to localhost:8000
npm run dev
```

Needs the backend running (`chhaya-backend/`, see its README) for anything
past the login screen to actually work.

## How it's organized

```
src/
  api/            one file per backend resource (auth.js, referenceSources.js)
                   + client.js, the shared axios instance with the auth header
  context/        AuthContext — who's logged in, available anywhere via useAuth()
  components/
    layout/       Sidebar, Topbar, AppShell — every logged-in page is these three
    ui/           Button, Card, Badge, Field — thin wrappers around the .btn/.card/etc
                   classes so the class names only live in one place
    icons/        Icon.jsx — one <svg> shape per icon, everything else reuses it
    reference-sources/   AnalysingPanel — shared between the add-source flow and
                   the detail page's processing state
  pages/
    auth/          Login, Signup — NOT in the original Figma export, see below
    reference-sources/   the 5 converted screens (List, AddSource, Detail)
    ComingSoonPage.jsx    placeholder for the other 3 members' modules
  styles/
    theme.css       design tokens (colors, fonts) copied from the Figma :root block
    components.css  every shared class (.card, .btn, .sidebar, .step, ...) from the export
```

**Why organized this way:** a page component should mostly just be markup
+ which API calls to make. Anything reused across screens (the sidebar, a
button, an icon) moved into its own file so the next person adding a
screen composes from these instead of copy-pasting a whole mockup file
and hand-editing it.

## What's real vs. placeholder

Only **Reference Sources** (Mahidad's Feature 1) is wired to the backend —
`/sources`, `/sources/new`, `/sources/:id`. The rest of the sidebar
(Style library, Study guides, Concept maps, Mock exams, Settings) points
at `ComingSoonPage`, a one-line placeholder, so the nav doesn't 404 while
those modules get built by the rest of the team on the same pattern (see
the backend README's "Adding a new module" section for the matching
backend steps — each new page here should pair with one new module there).

## Changes and additions made converting from the Figma export

**1. Logo swap.** The export used a heartbeat/"pulse" icon
(`<path d="M2 12h3l2-6 3 13 3-9 2 4h7"/>`) as a placeholder brand mark.
Replaced with your jar logo. Two processed versions ship in `src/assets/`:
`logo-black.png` (transparent background, for light surfaces) and
`logo-white.png` (white silhouette, transparent background, for the dark
sidebar/auth screen). The sidebar's brand-mark background also changed
from solid green to white specifically so the logo's black linework
stays visible — black-on-green at 32px would have nearly disappeared.
Both variants + a couple of intermediate files are in the top-level
`logo-assets/` folder if anyone needs to drop the logo into their own
mockups later.

**2. Auth screens.** Not in the Figma export — the mockups start after
login. `LoginPage`/`SignupPage` are built to the same tokens (colors,
radii, font) so they don't look bolted on, but the layout is mine, not
the designer's. Worth a real Figma pass whenever there's time.

**3. Five screens collapsed into three routes.** The export had 5 static
HTML files for one conceptual flow: empty list → add source → analysing
→ ready → error. Those last four are really *states of two pages* (a
form, and a detail view), not five separate destinations — so:
- `mahidad-f1-01-empty.html` → `/sources` (also handles the populated
  list, which the export didn't have a screen for — see #4)
- `mahidad-f1-02-add-source.html` → `/sources/new`
- `mahidad-f1-03/04/05` (analysing / ready / error) → all one route,
  `/sources/:id`, rendered conditionally based on the source's `status`
  field from the API

This isn't just fewer files — it's more correct. "Analysing" and "ready"
aren't different pages a user navigates between, they're the same
resource at different points in time, so one component driven by
`status` matches reality better than three static routes would.

**4. List view's populated state is a new design.** The export only
included the empty state for `/sources`. The card grid shown once
sources exist reuses existing classes (`.thumb`, `.src-title`, badges)
rather than inventing a new visual language, but it wasn't in the
original file — flag it for a design pass if the grid layout isn't quite
what you had in mind.

**5. The "analysing" screen is honestly simplified.** The mockup shows 5
granular steps with live per-lecture percentages — that assumes a
background worker streaming fine-grained progress. The current backend
runs ingestion inside one blocking request (see the backend README), so
the frontend only ever knows "in progress" or "done", not which of 5
sub-steps it's on. Rather than fake a percentage the backend isn't
reporting, `AnalysingPanel` shows an honest indeterminate progress bar
and two coarse phases. Once ingestion becomes a background task (the
backend is already structured for that swap), this is the component to
expand back into the full step-by-step breakdown.

**6. The error screen lost its lecture-by-lecture table.** The mockup's
`mahidad-f1-05-transcript-error.html` assumes a playlist (21 of 24
lectures succeeded, shows a per-lecture table). The current backend only
ingests a single video, so partial success isn't possible yet — a source
either fully succeeds or fully fails. The detail page's failed state
shows the real error message from the backend instead. That table is
worth rebuilding once playlist ingestion exists.

**7. Add-source form: some fields are decorative.** Teacher, Course, and
the transcript-cleaning checkboxes exist visually (matching the mockup)
but are disabled with a "coming soon" hint — the backend's
`ReferenceSourceCreate` schema doesn't accept them yet. Only source name,
URL, and source type actually submit. Extending the schema + form
together is a clean small task for whoever picks it up next.

## A note on state management

Everything here is `useState` + `useEffect` + polling
(`SourceDetailPage` re-fetches every 2.5s while status is
pending/processing). No React Query, no Redux. That's a deliberate
choice for a 4-person team learning the stack under a 2-month deadline —
it's more code per page than a data-fetching library would need, but
every line is either React or a `fetch`-like call, nothing to learn
beyond that. Worth revisiting if polling-heavy pages start feeling
repetitive once Group 4's Interactive Tutor Chat needs real-time updates
too.

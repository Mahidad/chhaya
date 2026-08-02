# Chhaya Backend

FastAPI backend, structured in layers so that four people can build four
different modules without stepping on each other, and so the code holds
up in a live no-AI implementation exam.

## Why layers, and not just routes.py + models.py

FastAPI on its own gives you almost nothing besides "write a function,
put a route decorator on it." Nothing stops you from writing your DB
queries, your Gemini calls, and your HTTP response shaping all inside one
route function. That's fine for a 10-minute demo. It falls apart at
20 features / 4 people / 2 months, for a concrete reason: **that route
function becomes the only place that logic exists**, so nobody else can
reuse it, nobody can test it without spinning up a server, and merge
conflicts pile up because everyone's editing the same kind of giant file.

Think of it like a restaurant kitchen:

| Layer | Restaurant equivalent | Job | Rule |
|---|---|---|---|
| **`api/` (routers)** | The waiter | Takes the order, checks it's a valid order, brings back a response | Never touches the DB directly, never contains business logic |
| **`schemas/`** | The order slip | Defines exactly what a valid request/response looks like | Pydantic only, no DB code |
| **`services/`** | The head chef | Decides *what happens*: fetch a transcript, call Gemini, save a profile | Never imports FastAPI or `Request`; framework-agnostic |
| **`repositories/`** | Pantry staff | Only fetches/stores rows. `get`, `create`, `update`, `delete` | The *only* layer allowed to write `db.query(...)` |
| **`models/`** | Recipe cards | The actual DB table shape (SQLAlchemy) | No logic, just columns and relationships |
| **`core/`** | Kitchen infrastructure | Config, DB engine, JWT/password logic | Everything else depends on this, this depends on nothing else |

The waiter never cooks. The chef never bikes to the farmers market
themselves (that's the repository's job). If today the "farmers market"
is Postgres and next month it needs to be a cache, only the repository
changes — the chef's recipe (business logic) doesn't care where the
ingredients came from.

**Why this matters for your specific exam constraint:** the evaluator
wants to see you build CRUD, DB schema, auth, and API integration live,
without AI. `BaseRepository` (`app/repositories/base.py`) *is* that
reusable CRUD pattern. Once you've written it once, adding a new table
(quizzes, flashcards, bookmarks — anything Group 2/3/4 needs) is: define
the model, define the schema, write a two-line repository subclass, write
a router. That's a pattern you can reproduce from memory under exam
pressure, because you'll have done it four times already by the time you
sit the exam.

## What's built as the working template (Feature 1 — Reference Sources)

`POST /api/v1/reference-sources` → creates a source → fetches the
YouTube transcript → sends it to Gemini for style analysis → stores a
`TeacherProfile`. Every layer above is exercised by this one feature, so
it's the pattern to copy for the next 19.

**Deliberate simplifications, stated so you don't mistake them for bugs:**
- Only single-video sources are ingested end-to-end right now; playlist
  crawling (enumerate every video in a playlist) is a clearly marked TODO
  in `reference_source_service.py`. Don't build that until the core
  pattern is solid across all four modules.
- Ingestion runs synchronously inside the request. Fine for one video
  (a few seconds); for a playlist you'll want `BackgroundTasks` so the
  "analysing" screen polls instead of the request hanging. The `status`
  field and the polling `GET /reference-sources/{id}` endpoint already
  exist so that change won't touch the API contract, only what happens
  inside `create_and_process`.
- If `GEMINI_API_KEY` is empty in `.env`, style analysis returns a
  realistic mock instead of failing, so the rest of the team isn't
  blocked waiting on someone's API key. Swap it in later — nothing else
  changes.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then fill in JWT_SECRET_KEY at minimum
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` — every endpoint is testable there,
including the "Authorize" button (it uses the `/auth/login` form).

Defaults to SQLite (`chhaya.db`, created automatically) so there's zero
setup to get running. To point at Postgres instead, set in `.env`:
```
DATABASE_URL=postgresql+psycopg2://chhaya:chhaya@localhost:5432/chhaya
```

## Adding a new module (the pattern to repeat)

Say Omar is building "Upload Past Exam Papers OCR":

1. `app/models/exam_paper.py` — the table (id, user_id, file_path, ocr_text, status...)
2. Add the import to `app/models/__init__.py`
3. `app/schemas/exam_paper.py` — `ExamPaperCreate`, `ExamPaperOut`
4. `app/repositories/exam_paper_repository.py` — subclass `BaseRepository`, add any custom queries
5. `app/services/exam_paper_service.py` — the OCR + business logic, calling the repository
6. `app/api/v1/endpoints/exam_papers.py` — the router, calling the service
7. One line in `app/api/v1/api.py`: `api_router.include_router(exam_papers.router)`

Every module follows this same seven-step shape. That consistency is
worth more than any individual clever bit of code — it's what makes the
codebase reviewable by teammates who didn't write that particular file,
and reproducible by hand in an exam.

## Migrations (Alembic)

Alembic is wired up (`alembic/env.py` reads `DATABASE_URL` from the same
`.env` everything else uses). Once your schema stabilizes:

```bash
alembic revision --autogenerate -m "add reference sources and teacher profiles"
alembic upgrade head
```

Until then, the `Base.metadata.create_all()` call in `main.py`'s startup
event auto-creates any missing tables, which is faster while the schema
is still changing shape daily.

## Tests

No formal test suite yet, but every endpoint here was verified with
FastAPI's `TestClient` during development (signup → login → JWT-protected
routes → create/list/poll a reference source → graceful failure when the
transcript can't be fetched). Worth setting up `pytest` + a `tests/`
folder mirroring this structure once Group 1 hands this off.

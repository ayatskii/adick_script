# Edvibe Grader — Design Spec

- **Date:** 2026-06-16
- **Status:** Draft (awaiting user review)
- **Owner:** Adilet ("Mister Adilet")
- **Topic:** Locally-run web app that runs and supervises an automated homework-grading bot for edvibe.com

---

## 1. Overview

**Edvibe Grader** is a single-user, locally-run web application that drives and supervises an
automated homework-grading bot for the [edvibe.com](https://edvibe.com) English-teaching platform.

For **Mr. Adilet's students in the "Pre-IELTS" marathon**, the bot:

1. Logs into edvibe.com.
2. Finds students whose lessons are in **"Awaiting"** status.
3. Opens each pending lesson and, for every **manual-grade** exercise:
   - **Audio answers** → download recording → transcribe → evaluate.
   - **Text answers** → extract → evaluate.
   - **Auto-checked** exercises → skipped (already graded by the platform).
4. Enters a **score (0–10) + short English comment** in the grade modal.
5. Marks the lesson complete (**"Завершить урок"**).

The default execution engine is **full-auto** (grade + complete), but a local web UI sits on top so
the teacher can configure runs, watch them live, **review/override** proposed grades, audit every
action, and reconcile what was changed on the platform.

### 1.1 Goals

- Cut the manual time the teacher spends grading repetitive Pre-IELTS homework.
- Keep the teacher in control: nothing about a run is opaque or unauditable.
- Make irreversible actions (submitting a score, completing a lesson) safe by default.

### 1.2 Non-goals (v1)

- Grading marathons other than Pre-IELTS, or students of other curators.
- Multi-user / hosted / cloud deployment. This is **localhost, single user**.
- Replacing the teacher's judgment — the AI proposes; the teacher can always override.
- Using the Edvibe School API for grading (no grading API exists; see §4.3).

---

## 2. Context & constraints

These shaped the design and are recorded so future readers understand the "why".

| Constraint | Implication |
|---|---|
| **No browser-automation MCP is connected yet.** | The plan's prior "live exploration" findings cannot be re-verified. Selectors in the original plan are explicitly guesses. → **Phase 0** is a read-only live exploration (once a Playwright MCP is connected) that captures verified selectors + the audio mechanism before any action code exists. |
| **No School API token (UUID) available.** | The fast `/api/Marathon/*` discovery path is **cut from v1**. Discovery is done by Playwright scraping the progress modal. Noted as a future enhancement if a token is obtained. |
| **OpenAI API key is available.** | OpenAI is used for **both** audio transcription and text/answer evaluation. |
| **Full-auto chosen as default mode.** | Because actions are irreversible, the bot ships with mandatory rails: dry-run, idempotency ledger, audit trail, blast-radius caps, fail-safe-on-uncertainty. |
| **Prior accidental grading.** | A previous exploration agent graded exercises and completed **Lesson 14 for student "Анель"**. The app includes a **reconcile** view to surface such leftovers. Future runs must never repeat this (read-only exploration, idempotency). |
| **Credential hygiene.** | `crednetials.json` is currently untracked plaintext at repo root. Phase 1 gitignores it and moves secrets to `.env`. Secrets never leave the local machine. |

---

## 3. Architecture

Two layers: a **bot core** (Python library, no UI) and a **local web app** (FastAPI backend +
React frontend) that drives it.

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (localhost UI)  —  React + Vite + TS + Tailwind     │
│   Dashboard · New Run · Live Monitor · Review Queue · ...     │
└───────────────▲───────────────────────────┬─────────────────┘
                │ REST + WebSocket           │
┌───────────────┴───────────────────────────▼─────────────────┐
│  FastAPI backend (localhost)                                 │
│   - REST API (runs, queue, students, settings, audit)        │
│   - WebSocket (live run events + log stream)                 │
│   - Background worker that executes a run                    │
└───────────────┬──────────────────────────────────────────────┘
                │ in-process calls
┌───────────────▼──────────────────────────────────────────────┐
│  Bot core (Python)                                            │
│   auth · scraper · evaluator · grader · state · audit         │
│   drives Playwright (server-side) + OpenAI                    │
└───────────────┬───────────────────────┬──────────────────────┘
                │                        │
        ┌───────▼────────┐      ┌────────▼────────┐
        │ Playwright →   │      │ OpenAI API      │
        │ edvibe.com     │      │ (transcribe+eval)│
        └────────────────┘      └─────────────────┘
                │
        ┌───────▼────────┐
        │ SQLite (local) │  runs · queue · ledger · audit
        └────────────────┘
```

### 3.1 Why this stack

- **Python + Playwright (sync API)** — the grading flow is inherently sequential and the
  irreversible actions must never run in parallel; the sync API keeps control flow obvious.
- **FastAPI** — same language family as the bot, first-class async + WebSocket for live progress.
- **React + Vite + TypeScript + Tailwind + shadcn/ui** — a polished, manageable operator UI; the
  design tooling target. (Alternative considered: HTMX + Jinja + Tailwind — simpler, server-rendered,
  fewer deps, but less polished. Rejected for v1 because a good-looking management UI was a stated goal.)
- **SQLite** — zero-config local persistence; powers idempotency, resume, audit, and history.

---

## 4. Bot core

### 4.1 Module layout

```
edvibe_bot/
├── config.py            # env + constants (marathon, curator, models, score scale, thresholds)
├── runner.py            # orchestrates a full run; emits events for the web layer
├── auth/login.py        # login + Playwright storage_state reuse (skip re-login)
├── scraper/dashboard.py # classes → Марафоны → Pre-IELTS → filter by curator
├── scraper/progress.py  # open "Прогресс ученика" → list lessons + statuses → find "Awaiting"
├── scraper/lesson.py    # open lesson → sections → exercises → classify type
├── evaluator/audio.py   # resolve audio source → download blob → transcribe (OpenAI)
├── evaluator/text.py    # evaluate transcript/text → Evaluation (OpenAI, structured output)
├── evaluator/prompts.py # Pre-IELTS rubric prompts per exercise type
├── evaluator/schema.py  # pydantic Evaluation model
├── grader/poster.py     # grade modal: score + comment → save; then Завершить урок
├── state/store.py       # SQLite ledger keyed (student, lesson, exercise) → idempotency/resume
├── audit/log.py         # structured log + append-only audit JSONL of every action
└── selectors.py         # verified selectors captured in Phase 0 (single source of truth)
```

Refinements vs. the original plan: added **`state/store.py`** (idempotency/resume — original had
none; a mid-run crash would otherwise re-grade) and **`audit/log.py`** (immutable record of every
submit/complete — essential after the Анель incident), plus **`selectors.py`** so every selector
lives in one verified place rather than scattered through scraper code.

### 4.2 Control flow (per run)

```
load config + validate prerequisites (fail fast if creds / OPENAI_API_KEY missing)
launch Playwright (headed if requested); restore storage_state, re-login if expired
navigate: classes → Марафоны → Pre-IELTS → Фильтр → Curator "Mister Adilet" → Apply
for each student (respect scope + --max-students):
    open "Прогресс ученика"; parse lessons; collect "Awaiting"
    for each awaiting lesson (respect --max-lessons):
        if ledger says lesson already completed by us → skip
        open lesson ("Открыть урок")
        for each exercise across sections:
            classify: auto-checked → skip | manual-grade (audio | text)
            if ledger says exercise already graded by us → skip
            gather: audio → download blob → transcribe ; text → extract
            evaluate via OpenAI → Evaluation(score 0–10, comment EN, rationale, confidence)
            record proposal in ledger + audit
            decide: dry-run OR confidence < threshold OR fetch/parse failed
                    → flag, do NOT submit
                    else → open grade modal, enter score + comment, save ("Продолжить")
        if not dry-run AND all manual exercises handled (none flagged-blocking)
            → "Завершить урок"; record completion
emit run report (graded / skipped / flagged / errors)
```

### 4.3 Discovery (pure Playwright)

Without a School API token, discovery scrapes the **"Прогресс ученика"** modal per student to read
the status icons and identify "Awaiting" lessons. The 43-student list is read from the filtered
marathon view. (Future enhancement: `GET /api/Marathon/GetMarathonStudents?Filter=1` if a token is
obtained, to skip per-student modal scraping.)

### 4.4 Evaluation

- **Transcription:** `gpt-4o-transcribe` (fallback `whisper-1`) on the downloaded audio blob.
- **Scoring:** `gpt-4o` with **structured JSON output** so every call returns a clean object — no
  free-text parsing. Schema in §6.
- **Rubric:** Pre-IELTS level (CEFR ~A2–B1 target). Per-type prompts in `prompts.py`:
  - *Speaking / Shadowing (audio):* task response, pronunciation, fluency.
  - *Writing / Grammar (text):* grammar accuracy, vocabulary range, task completion.
- **Output:** integer **0–10** score + a 1–2 sentence constructive **English** comment, plus a
  `confidence` used by the fail-safe rule.

### 4.5 Audio handling (unverified until Phase 0)

Edvibe recordings may be token-protected streams. Phase 0 must confirm the audio can actually be
fetched (direct media URL vs. authenticated blob via the Playwright context). **If it cannot be
fetched, audio exercises degrade to "flag for manual review"** rather than being blindly scored.

---

## 5. Safety rails (mandatory, because default is full-auto)

- **`dry-run` mode** — evaluate + log proposed grades, submit nothing. **The first real run must be
  `dry-run`, headed, scoped to a single student.**
- **Idempotency ledger** (SQLite, keyed `(student_id, lesson_id, exercise_id)`) — never re-grade or
  re-complete a recorded item; enables crash-safe resume.
- **Blast-radius caps** — `max_students`, `max_lessons`; default canary = 1 lesson.
- **Fail-safe rule** — any uncertainty (audio fetch fail, parse fail, `confidence < threshold`,
  selector not found) → **skip + flag**, never a fabricated score; clamp scores to 0–10.
- **Audit trail** — append-only JSONL + SQLite recording every evaluation and every submit/complete
  with timestamps and the dry-run flag.
- **Reconcile (read-only)** — report what is currently marked complete on the platform, highlighting
  bot-completed lessons, so leftovers (e.g. Lesson 14 / Анель) are visible.
- **Human-like pacing** + **screenshot-on-error** saved to `reports/`.

---

## 6. Data model (SQLite)

```
runs(id, mode, scope_json, started_at, finished_at, status,
     counts_json)                          -- graded/skipped/flagged/errors
ledger(student_id, lesson_id, exercise_id, -- PK = the triple
       student_name, lesson_name, exercise_no, type,
       proposed_score, proposed_comment, confidence,
       submitted, submitted_at, dry_run, run_id, status)  -- status: graded|skipped|flagged|error
queue(id, run_id, student_id, lesson_id, exercise_id,     -- review-queue items
      transcript_or_answer, proposed_score, proposed_comment,
      confidence, decision)               -- pending|approved|rejected|edited
audit(id, ts, run_id, actor, action, target_json, detail_json)  -- append-only
settings(key, value)                       -- non-secret prefs; secrets live in .env
```

`Evaluation` (pydantic, returned by the evaluator):

```python
class Evaluation(BaseModel):
    score: int            # 0–10, clamped
    comment: str          # English, 1–2 sentences
    rationale: str        # internal, not shown to student
    confidence: float     # 0–1
```

---

## 7. Web app

### 7.1 Backend API (FastAPI, localhost only)

```
POST   /api/scan                 # read-only discovery → inventory of Awaiting work
GET    /api/students             # students + awaiting-lesson counts
POST   /api/runs                 # start a run {mode, scope, caps, headed, threshold}
GET    /api/runs                 # list runs
GET    /api/runs/{id}            # run detail / timeline
POST   /api/runs/{id}/stop       # cancel a running job
WS     /api/runs/{id}/stream     # live events + log lines
GET    /api/queue                # review-queue items
POST   /api/queue/{id}/decision  # approve | reject | edit (score/comment)
POST   /api/queue/submit         # submit approved items to edvibe
GET    /api/flagged              # items the bot refused to auto-grade
GET    /api/reconcile            # read-only "what's completed on platform"
GET    /api/audit                # audit log
GET/PUT/api/settings             # non-secret prefs; secrets via .env only
```

The bot run executes in a **background worker**; Playwright runs server-side. Run events are pushed
over WebSocket so the Live Monitor updates in real time.

### 7.2 Frontend screens

UI chrome is **English**; Edvibe's Russian labels (Марафоны, Прогресс ученика, Завершить урок) and
real lesson/section names appear as **data**.

1. **Dashboard** — pending-work stat cards, last-run status, "Start run", recent runs, advisory banner.
2. **New Run** — mode (Dry-run / Full-auto / Review-queue), scope (all of Mr. Adilet's students or
   pick), caps, headed toggle, confidence-threshold slider; mode-aware confirm (Full-auto → amber
   confirm dialog).
3. **Live Monitor** — real-time Student▸Lesson▸Exercise tree, streaming log console, per-exercise
   status chips, error screenshots, Stop.
4. **Review Queue** — proposed score + English comment per exercise (**editable**), audio player +
   transcript / written answer, confidence, Approve/Reject, bulk approve, sticky submit footer.
5. **Students** — inventory of awaiting lessons per student; "Run for this student".
6. **History / Audit** — past runs + full timeline (proposed vs submitted, dry-run flag, who edited);
   **Reconcile** tab.
7. **Flagged** — items needing manual attention with reason + Retry.
8. **Settings** — Edvibe creds, OpenAI key (masked, "stored locally only"), models, score thresholds,
   pacing, marathon/curator defaults, "dry-run by default" toggle.

### 7.3 Visual system

Professional EdTech ops tool: indigo/violet accent, neutral surfaces, Inter type, compact data
tables. Consistent status semantics: evaluating=blue, graded=green, skipped=gray, flagged=amber,
error=red, dry-run=dashed purple. Light + dark themes. Persistent top-bar RUN STATUS pill.
Full UI-generation prompt: see `2026-06-16-edvibe-grader-ui-prompt.md`.

---

## 8. Security & credentials

- Move `crednetials.json` → `.env` (`EDVIBE_LOGIN`, `EDVIBE_PASSWORD`, `OPENAI_API_KEY`); add a
  `.env.example`.
- `.gitignore`: `.env`, `crednetials.json`, `*.sqlite`, `storage_state.json`, `reports/`, audio cache.
- Bind the web server to `127.0.0.1` only. No auth beyond localhost (single user).
- Secrets are never logged, never sent anywhere except OpenAI (eval) and edvibe.com (login).

---

## 9. Error handling

- **Selector not found** → typed `SelectorError`, screenshot to `reports/`, abort *current lesson*
  cleanly (never half-grade), log, continue to next.
- **OpenAI error** → retry with backoff; persistent failure → flag + skip.
- **Network/navigation** → retry; refresh `storage_state` / re-login if session expired.
- **Global principle:** any uncertainty defaults to **not submitting**.

---

## 10. Testing strategy

- **TDD on pure logic:** ledger idempotency, `Evaluation` schema parsing, config validation,
  audio-source resolution (mocked), prompt formatting, score clamping.
- **Browser layers:** verified via a controlled **single-student dry-run**, reviewing the report;
  then a **single real "canary" lesson**; then scale.
- **API layer:** FastAPI route tests with the bot core mocked.

---

## 11. Implementation phasing

- **Phase 0 — Live exploration** *(needs Playwright MCP connected)*: read-only login, capture
  verified selectors + audio mechanism + relevant network calls → populate `selectors.py`. **No
  grading or completion actions.** De-risks the unverified-selector problem.
- **Phase 1 — Scaffold:** repo structure, config, auth (storage_state), `.gitignore` + credential
  hygiene (`crednetials.json` → `.env`).
- **Phase 2 — Discovery (read-only):** dashboard nav + filter + progress scraping → inventory report
  of who has Awaiting work.
- **Phase 3 — Lesson/exercise extraction (read-only):** sections, exercises, type classification.
- **Phase 4 — Evaluator:** audio transcription + text eval + Pre-IELTS prompts; unit-tested.
- **Phase 5 — Grader + state + audit:** score/comment posting + completion, behind dry-run; ledger
  + audit trail.
- **Phase 6 — Web app:** FastAPI backend + React UI + WebSocket live monitor + review queue + history
  + reconcile.
- **Phase 7 — End-to-end:** single-student dry-run → review → single real canary lesson → scale.

---

## 12. Open questions / risks

1. **Audio fetchability** (resolved in Phase 0) — if recordings are unfetchable, audio exercises
   become manual-review items.
2. **Selector stability** — Edvibe is a third-party SPA; selectors may change. `selectors.py`
   centralizes the blast radius of such changes.
3. **Platform anti-automation** — pacing + headed/headless behavior must avoid tripping protections;
   tune in Phase 7.
4. **Grading quality** — the teacher owns final responsibility; the Review Queue exists so quality can
   be spot-checked or fully gated even in full-auto.
5. **Phase 6 sequencing** — the web app can be built in parallel with the bot core against a mocked
   runner, but real value depends on Phases 0–5 being solid first.

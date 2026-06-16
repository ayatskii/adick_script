# Edvibe Scraper Refactor — Implementation Plan

> **For agentic workers:** execute task-by-task with review. Steps use `- [ ]` checkboxes. **Task R0 is a BLOCKING, human-supervised live capture — several later tasks depend on its output.**

**Goal:** Rework the bot's selectors + scraper + key derivation to match edvibe.com's *real* DOM (discovered in Phase 0), so the bot can actually find and grade awaiting homework — replacing the `data-testid`/`id-attribute` assumptions that don't exist on the live site.

**Why (Phase 0 findings):** edvibe is a Vue SPA with scoped CSS + utility classes + some semantic BEM classes. There are **no `data-testid` and no id attributes**; identifiers live in **URLs and visible text**; lesson "awaiting" status is **not** shown in the progress modal; the grade trigger/complete control are **divs (text-selectors only)**; audio answers are **direct fetchable MP3 URLs**; and scores are **out of 5 (per-exercise max), not 10**. Full detail: `docs/superpowers/specs/phase0-exploration-notes.md`.

**Scope:** `edvibe_bot/selectors.py`, `scraper/{dashboard,progress,lesson}.py`, `grader/poster.py`, `evaluator/{schema,text}.py` (score max), `runner.py` (key derivation), and their tests. The runner's safety rails, store, audit, CLI, and web/backend stay as-is.

---

## New selector & identity strategy (the core change)

| Concern | Old (wrong) | New (real) |
|---|---|---|
| Element hooks | `[data-testid=...]` | semantic **BEM classes** + **Playwright `text=` selectors** |
| Student id | `data-student-id` attr | **text** in the student row (`3176678`) and/or `?pupil=` in the lesson URL |
| Lesson id | `data-lesson-id` attr | **`/lesson/{lessonId}` segment of the URL** after opening |
| Exercise id | `data-exercise-id` attr | composite **`f"{lessonId}:{exerciseNumber}"`** (number is text "1.1") |
| Lesson "awaiting" | `.status--awaiting` | **unsolved — resolved in R0** (status not in progress modal) |
| Sections | `[data-testid=section]` | **`?section=n` query param** + section names text |
| Exercise block | `[data-testid=exercise]` | **`.exercise-wrapper`** |
| Audio | `audio` (ok) | `audio` → read **`.currentSrc`** (direct `media-a.edvibe.com/.../*.mp3`) |
| Grade trigger | `text=Оценить упражнение` (ok, but it's a **div**) | `text=Оценить упражнение` inside `.exercise-estimate-view` |
| Complete lesson | `text=Завершить урок` (ok, but a **div**) | `text=Завершить урок` |
| Score max | hardcoded 10 | **read per-exercise max live** (e.g. `/5`) |

**Confirmed-good selectors** (keep): `LOGIN_*`, `LOGIN_URL`, `AUTHED_URL`, `text=Марафоны`, `text=Pre-IELTS`, `text=Фильтр`, `button:has-text("Применить")`, `text=Прогресс ученика`, `.marathon-modules-lessons-lesson-li`, `text=Открыть урок`, `text=Завершить урок`, `.exercise-wrapper`, `.exercise-estimate-view`, modal close `.icon.close`.

---

## Task R0 — Supervised live capture (BLOCKING; needs Playwright MCP + a human)

> Resolves the three gaps that need an actual *awaiting* (ungraded-submitted) exercise. Read-only except for opening the grade modal, which is **closed without submitting**. A human watches.

- [ ] **R0.1 — Awaiting discovery.** Determine how the bot finds homework that needs grading. Investigate, in order: (a) the marathon **"Урок"** tab (`/marathons/marathon/{id}/...`), (b) any teacher "homework to check" / notifications view, (c) whether `GetMarathonStudents?Filter=1` (School API) is usable (needs the UUID token), (d) fallback: open each lesson and detect exercises whose `.exercise-estimate-view` shows a clickable "Оценить упражнение" with **no score**. Pick the cheapest reliable mechanism and document it.
- [ ] **R0.2 — Find one ungraded exercise**, open its grade modal (click `text=Оценить упражнение`), and capture: the score input selector + its **max** (is it always /5 or per-exercise?), the comment field selector, the save/confirm control text (`Продолжить`?), and the modal container class. **Close without saving** (`.icon.close`/Escape).
- [ ] **R0.3 — Curator filter.** Open Фильтр → "Кураторы", capture the curator option selector and confirm the real curator name for this account ("Mister Adilet"?).
- [ ] **R0.4 — Audio fetch check.** Confirm `context.request.get(currentSrc)` returns the MP3 bytes (200) using the logged-in Playwright context (cookies).
- [ ] **R0.5 —** Record all of the above into `phase0-exploration-notes.md` and into the constants below.

---

## Task R1 — Rewrite `edvibe_bot/selectors.py`

- [ ] Replace the `data-testid` guesses with the real values; **remove** `STUDENT_ID_ATTR`, `LESSON_ID_ATTR`, `EXERCISE_ID_ATTR` (no such attributes). Add URL-pattern constants/helpers instead.

```python
# Login / URLs (confirmed)
LOGIN_URL = "https://edvibe.com/login"
AUTHED_URL = "https://edvibe.com/cabinet/school/classes"
LOGIN_EMAIL = "input[type=email]"
LOGIN_PASSWORD = "input[placeholder='Password']"
LOGIN_SUBMIT = "button:has-text('Log in to your account')"

# Marathon nav + filter (confirmed)
MARATHONS_TAB = "text=Марафоны"
PRE_IELTS_CARD = "text=Pre-IELTS"
FILTER_BUTTON = "text=Фильтр"
FILTER_APPLY = "button:has-text('Применить')"
CURATOR_OPTION = "<<R0.3>>"            # curator pick inside "Кураторы"

# Students (id/name are TEXT; no attributes)
STUDENT_PROGRESS_BTN = "text=Прогресс ученика"
STUDENT_ROW = "<<R0/confirm: marathon student card class>>"

# Progress modal + lessons (confirmed)
PROGRESS_MODAL = ".marathon-student-progress-modal"
PROGRESS_MODAL_CLOSE = ".marathon-student-progress-modal .icon.close"
LESSON_ROW = ".marathon-modules-lessons-lesson-li"
LESSON_OPEN_BUTTON = "text=Открыть урок"
# lesson name = LESSON_ROW innerText first line ("Lesson 14: Entertainment")

# Lesson view (confirmed)
LESSON_LAYOUT = ".lesson-layout.marathon-lesson-layout"
EXERCISE_BLOCK = ".exercise-wrapper"
EXERCISE_AUDIO = "audio"               # read .currentSrc
GRADE_ESTIMATE_VIEW = ".exercise-estimate-view"
GRADE_EXERCISE_BTN = "text=Оценить упражнение"   # a div, NOT a button
COMPLETE_LESSON_BTN = "text=Завершить урок"      # a div, NOT a button
# section switch: append ?section=n to the lesson URL

# Grade modal (from R0.2)
SCORE_INPUT = "<<R0.2>>"
COMMENT_INPUT = "<<R0.2>>"
GRADE_SAVE_BTN = "<<R0.2 e.g. text=Продолжить>>"

# URL patterns (identity source)
import re
LESSON_URL_RE = re.compile(r"/marathon/(\d+)/lesson/(\d+)")   # (marathon_id, lesson_id)
PUPIL_QS = "pupil"   # ?pupil={student_id}
```
- [ ] Update `tests/test_selectors.py` REQUIRED list to the new names; drop the removed `*_ID_ATTR`.

---

## Task R2 — `scraper/dashboard.py`
- [ ] `open_marathon`: navigate `AUTHED_URL` → click `MARATHONS_TAB` → click `PRE_IELTS_CARD` → (optional) `FILTER_BUTTON` → `CURATOR_OPTION` → `FILTER_APPLY`. Use Playwright text selectors; handle the duplicate-Фильтр strict-mode by scoping to the visible/marathon one.
- [ ] `list_students`: read each student card; **id from the displayed numeric text**, name from the name paragraph. Return `Student(id, name)`. (No id attribute — parse text; the row class to confirm in R0.)

## Task R3 — `scraper/progress.py`
- [ ] `open_progress(student)`: click that student's `STUDENT_PROGRESS_BTN` (scope by the student's card).
- [ ] `list_lessons`: from `.marathon-modules-lessons-lesson-li`, lesson **name = first text line** ("Lesson N: Title"); lesson number parsed from the name.
- [ ] `awaiting_lessons`: **rework per R0.1** — the progress modal does NOT mark awaiting; implement the chosen discovery mechanism (tab / per-exercise scan / API). This replaces the old `.status--awaiting` check.
- [ ] `open_lesson(lesson)`: click its `Открыть урок`; this **navigates** to `/marathon/{m}/lesson/{lessonId}?pupil={pupilId}`. After navigation, parse `lessonId` via `LESSON_URL_RE` and `pupilId` via the `pupil` query param — these become the stable ids.

## Task R4 — `scraper/lesson.py`
- [ ] Iterate sections by appending `?section=n` (n=0..N-1) to the lesson URL (or click the section list).
- [ ] `list_exercises`: from `.exercise-wrapper`; `number` = text "1.1"/"1.2"; `prompt_text` = question text; `audio_url` = the inner `audio`'s `.currentSrc` (None if no audio); `answer_text` for text answers; **graded?** = `.exercise-estimate-view` shows a score (`N/M`) vs a clickable "Оценить упражнение" with no score; `score_max` parsed from the `N/M` or the modal.
- [ ] `Exercise` gains `score_max: int | None` and `is_graded: bool`. `element_id` = `f"{lesson_id}:{number}"` (composite, stable).

## Task R5 — Idempotency keys (`runner.py`)
- [ ] Derive `exercise_id = ex.element_id` (now `"{lessonId}:{number}"`, always present) and `lesson_id`/`student_id` from the URL/text. The `no_stable_id` FLAG now only triggers if number/lesson_id genuinely can't be parsed. Keep all other safety rails unchanged. Skip exercises where `is_graded` is already True.

## Task R6 — Score scale (`evaluator/schema.py`, `evaluator/text.py`, `grader/poster.py`)
- [ ] Remove the hardcoded 0–10 clamp assumption. Thread the per-exercise **`score_max`** (e.g. 5) into the evaluation + the grade-modal fill, clamp to `[0, score_max]`. Update the rubric prompt to request a score out of the real max.

## Task R7 — `grader/poster.py`
- [ ] `grade_exercise`: if dry_run return; else click `GRADE_EXERCISE_BTN` (div, text selector) within the exercise's `.exercise-estimate-view`, fill `SCORE_INPUT` (clamped to `score_max`) + `COMMENT_INPUT`, click `GRADE_SAVE_BTN` (selectors from R0.2). `complete_lesson`: click `COMPLETE_LESSON_BTN`. Keep dry-run gating + the in_progress→terminal durability exactly as the runner expects.

## Task R8 — Audio (`evaluator/audio.py`)
- [ ] `download_audio(context, url)`: `context.request.get(url)` against the `media-a.edvibe.com` MP3 (confirmed direct URL in R0.4); return bytes or None. No change to `transcribe`.

## Task R9 — Tests + integration
- [ ] Update the scraper/runner unit tests' fakes to the new DOM shapes (BEM classes, URL-derived ids, `score_max`, `is_graded`). Keep the runner safety tests.
- [ ] Re-run a supervised **single-student dry-run** end-to-end against the live site (read-only/dry-run), confirm it discovers awaiting work (R0.1), evaluates, and submits NOTHING. Then remove any remaining `# CONFIRM` and flip `phase0_done`.

---

## Execution order
**R0 (supervised) → R1 → (R2, R3, R4 in sequence; they share the scraper flow) → R5 → R6 → R7 → R8 → R9.** R7 and the `awaiting_lessons` part of R3 are hard-blocked on R0.2/R0.1 respectively.

## Risks / notes
- **Awaiting discovery (R0.1) is the biggest unknown** and gates real usefulness — resolve it first.
- Selectors are text/Russian-label based → resilient to CSS hash changes but sensitive to UI copy changes; centralised in `selectors.py`.
- Score scale varies (`/5`) — do not assume 10 anywhere.
- The web/backend/runner-safety layers are unaffected; this refactor is confined to discovery + extraction + the grade action.

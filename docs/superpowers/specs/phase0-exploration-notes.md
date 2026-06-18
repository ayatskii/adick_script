# Phase 0 — Live exploration notes (edvibe.com)

- **Date:** 2026-06-16
- **Account:** beknurmanadilet@gmail.com (Mr. Adilet) — read-only exploration via Playwright MCP.
- **Marathon:** Pre-IELTS (id `110326`), 203 students, 29 lessons/modules.
- **Outcome:** ⚠️ The planned `data-testid`-based selectors do NOT match the real DOM. Phase 0 is **not a value-swap** — it surfaced that the selector strategy and parts of the scraper need rework. Details below. **No grading or lesson completion was performed.**

## What was confirmed (works against the live site)

| Selector | Confirmed value | Notes |
|---|---|---|
| `LOGIN_URL` | `https://edvibe.com/login` | ✓ |
| `AUTHED_URL` / `NAV_CLASSES` | `https://edvibe.com/cabinet/school/classes` | ✓ landed here post-login |
| `LOGIN_EMAIL` | `input[type=email]` | ✓ unique |
| `LOGIN_PASSWORD` | `input[placeholder="Password"]` | ✓ (a 2nd hidden `input[type=password]` exists, so `input[type=password]` alone is ambiguous) |
| `LOGIN_SUBMIT` | `button:has-text("Log in to your account")` | ✓ (4 `button[type=submit]` on the page) |
| `MARATHONS_TAB` | `text=Марафоны` | ✓ a filter pill (`?type=2`) |
| `PRE_IELTS_CARD` | `text=Pre-IELTS` | ✓ marathon card → `/marathons/marathon/110326/students` |
| `FILTER_BUTTON` | `text=Фильтр` | ✓ button present on the students page |
| `STUDENT_PROGRESS_BTN` | `text=Прогресс ученика` | ✓ one per student row |
| `LESSON_ROW` | `.marathon-modules-lessons-lesson-li` | ✓ semantic BEM class |
| `LESSON_OPEN_BUTTON` | `text=Открыть урок` or `.marathon-student-progress-lesson-actions__go-to-lesson` | ✓ |
| (progress modal) | `.tir-modal.marathon-student-progress-modal` | ✓ container |

## The core finding — DOM reality

Edvibe is a **Vue SPA** with:
- **Scoped CSS** (`data-v-XXXX` attributes) — build-specific, NOT usable as stable selectors.
- **Utility/atomic classes** (`f`, `cg-2`, `ai-c`, `w-100`, `fd-col`, `py-3`) — not unique.
- **Some semantic BEM classes** (`marathon-modules-lessons-lesson-li`, `status`, `info`, `avatar-li`, `marathon-student-progress-lesson-actions__go-to-lesson`) — these ARE usable.
- **No `data-testid` anywhere.**
- **No id attributes** for student / lesson / exercise. Identifiers appear only as **visible text**: student id `3176678` (text), lesson `"Lesson 14: Entertainment"` (text), etc.

### Consequences for the bot (require rework, not value-swaps)
1. **`STUDENT_ID_ATTR`, `LESSON_ID_ATTR`, `EXERCISE_ID_ATTR` do not exist.** The scraper's idempotency keys must be **derived from visible text** (student numeric id text, lesson number, exercise number) — `block.get_attribute(...)` returns `None`, which the runner correctly treats as `no_stable_id` → FLAG. So with the current code the bot would flag everything and grade nothing.
2. **Lesson "Awaiting" status is CSS-driven, not text/attribute.** Every lesson row contains an **empty** `<div class="status"></div>`; the awaiting/done/not-started distinction is rendered via the scoped CSS (background/color), with no modifier class or text in the markup sampled. Detecting "awaiting" needs either a row **modifier class** (not yet located) or reading the **computed style** of `.status` — `LESSON_STATUS_AWAITING = ".status--awaiting"` is wrong.
3. **Selectors must be text-based or BEM-class-based**, never `data-testid`.

## Not yet explored (blocked on finding a genuinely "awaiting-grading" lesson, done safely)
- Curator filter internals: `CURATOR_OPTION`, `FILTER_APPLY` (need to open the Фильтр panel).
- Student-row class on the marathon list: `STUDENT_ROW`, `STUDENT_NAME` (no id attr — text only).
- Lesson view internals: `SECTION_NAV`, `EXERCISE_BLOCK`, `EXERCISE_NUMBER`, `EXERCISE_PROMPT`, `EXERCISE_AUDIO`, `EXERCISE_TEXT_ANSWER`, `GRADE_EXERCISE_BTN`, `COMPLETE_LESSON_BTN`.
- Grade modal internals: `SCORE_INPUT`, `COMMENT_INPUT`, `GRADE_SAVE_BTN` — these require opening the "Оценить упражнение" modal on a real awaiting exercise; to be done under supervision and closed WITHOUT submitting.
- Audio fetch mechanism (`download_audio`): need a "Голос записан" exercise to capture the media request.

## Recommended next steps
1. **Rework the selector strategy + scraper** to: locate rows/exercises by BEM class + text anchors; derive `student_id`/`lesson_id`/`exercise_id` from displayed text; detect "awaiting" via the row modifier class or computed style of `.status`.
2. **Find a real awaiting-grading lesson** (one of Mr. Adilet's students with submitted-but-ungraded homework) and, under supervision, capture the lesson-view + grade-modal + audio selectors (open the grade modal read-only, close without saving).
3. Only then remove the remaining `# CONFIRM` markers and flip `phase0_done` true.

## Deep research — lesson view, audio, ids, grading (round 2)

### Identifiers come from the URL (not attributes)
Opening a lesson navigates to:
`https://edvibe.com/marathon/{marathonId}/lesson/{lessonId}?pupil={pupilId}&section={n}`
- e.g. `/marathon/110326/lesson/1781437?pupil=3176678&section=0`.
- **`lessonId` (1781437)** and **`pupilId` (3176678)** are STABLE ids — read them from the URL after opening (and `pupilId` also appears as text in the student row). Sections are navigated by the `?section=n` query param (0-indexed).
- Marathon id is in the marathon URL (`/marathons/marathon/110326/...`).

### Lesson view structure (real classes)
- Lesson layout: `.lesson-layout.marathon-lesson-layout`.
- Sections list ("Разделы"): Entertainment discussion, Grammar, Vocabulary, Reading time., Shadowing (matches the design). Section switch = `?section=n`.
- Exercise block: **`.exercise-wrapper`** (`.exercise-common-ui-components`); inner blocks `.exercise-wrapper-block`. No `data-exercise-id` — the exercise **number** ("1.1", "1.2") is text inside the wrapper; pagination "1 из 6 / Далее".
- Exercise prompt: question text inside the wrapper.
- Grade widget: **`.exercise-estimate-view`** holds "Оценить упражнение:" + the score. When GRADED it shows e.g. "Оценить упражнение: 5/5". When UNGRADED, "Оценить упражнение" is the clickable trigger → opens the grade modal (NOT captured — see gap).
- **`GRADE_EXERCISE_BTN` and `COMPLETE_LESSON_BTN` are NOT `<button>` elements** — they are divs/spans with click handlers. Use Playwright text selectors (`text=Оценить упражнение`, `text=Завершить урок`), never `button:has-text(...)`.

### Audio mechanism — FETCHABLE ✅
- Voice-recorded answers ("Голос записан", with "00:00 / MM:SS") render a real `<audio>` element.
- `audio.currentSrc` is a **direct MP3 URL**: `https://media-a.edvibe.com/files/LessonExerciseAudioRecordings/{uuid}.mp3`.
- → `download_audio` can fetch bytes via the Playwright request context (carries the session). `EXERCISE_AUDIO = "audio"`, read `.currentSrc`/`.src`.

### Score scale — NOT 0–10
- Graded exercise shows **"5/5"** — scores are out of **5** (or a per-exercise max), not 0–10 as the design/spec assumed. The grade modal's max must be read live; the evaluator/clamp must use the real max, not a hardcoded 10.

### Confirmed in round 2
| Selector | Value |
|---|---|
| `FILTER_APPLY` | `button:has-text("Применить")` (filter has a "Кураторы" section; "Сбросить все"/"Отмена" present) |
| `EXERCISE_BLOCK` | `.exercise-wrapper` |
| `EXERCISE_AUDIO` | `audio` (read `.currentSrc`) |
| `GRADE_EXERCISE_BTN` | `text=Оценить упражнение` (div, not button) |
| `COMPLETE_LESSON_BTN` | `text=Завершить урок` (div, not button) |
| grade widget | `.exercise-estimate-view` |
| section switch | `?section=n` query param |

## Remaining gaps (need a SUPERVISED pass on a real *awaiting* exercise)
1. **Awaiting discovery is unsolved.** The progress modal does NOT visually distinguish awaiting lessons (all `.status` divs are empty/transparent for the sampled student). The bot cannot find "lessons needing grading" the way the plan assumed. Likely real approaches to evaluate: (a) the marathon **"Урок"** tab, (b) a teacher homework-checking/notifications view, (c) the School API `GetMarathonStudents?Filter=1` (needs the UUID token), or (d) brute-force: open each lesson and detect exercises whose `.exercise-estimate-view` has a clickable "Оценить упражнение" (no score yet). This must be resolved before the bot can target work.
2. **Grade modal internals** (`SCORE_INPUT`, comment field, save/Продолжить, the real max) — only visible by clicking "Оценить упражнение" on an UNGRADED exercise; capture under supervision, close WITHOUT submitting.
3. **Curator option** exact selector inside the "Кураторы" filter section, and whether "Mister Adilet" is the real curator name for this account.

**Safety:** the whole session was read-only. No exercise was graded, no lesson completed, no score submitted.

## Refactor R1–R9 — resolutions applied to the code (2026-06-16)

- **R0.1 Awaiting discovery — resolved.** Implemented as a per-exercise scan: an
  exercise (and therefore its lesson) is AWAITING when its `.exercise-estimate-view`
  shows the clickable "Оценить упражнение" with **no** "N/M" score. `progress.list_lessons`
  marks a lesson `awaiting` when any of its grade widgets is ungraded; `awaiting_lessons`
  stays a pure filter. The lessons-tab (`/marathons/marathon/{id}/lessons`) awaiting-count
  badge remains an optional future optimisation to skip 0-badge lessons.
- **Identity — resolved.** No id attributes. `student_id` = numeric text in the row
  (`STUDENT_ID_RE`); `lesson_id` = `/lesson/(\d+)` from the URL after open
  (`LESSON_URL_RE`); `pupil_id` = `?pupil=` query param; `exercise_id` (idempotency key)
  = composite `f"{lesson_id}:{number}"` where number is text "1.1". `no_stable_id` now
  fires only when number/lesson_id can't be parsed.
- **Score scale — resolved.** `Exercise.score_max` (read from the graded "N/M" widget; the
  modal max stays best-guess) threads through `EvalRequest.score_max` → the rubric prompt
  ("score 0-N") → the `Evaluation` clamp `[0, score_max]`. No hardcoded /10 remains
  (default fallback is 10 only when the live max is unknown).
- **Audio — confirmed.** `download_audio` = `context.request.get(currentSrc)`; reader uses
  `audio.currentSrc` (fallback `src`).

### R0.2 — RESOLVED: live capture on Nurdana Ardaqqyzy, Lesson 18 (2026-06-16)

Captured read-only on a real awaiting exercise (opened the grade modal, dumped its
DOM, closed with Escape — **nothing graded, nothing submitted**). Target: pupil
**3190603** (Nurdana Ardaqqyzy), lesson **1798271** ("Science and Innovations").

**Detection assumption from R0.1 was WRONG and is now corrected.**
`.exercise-estimate-view` renders **only for ALREADY-GRADED exercises** (it shows the
awarded "N/M"). An **ungraded** manual exercise has *no* estimate-view at all — its
marker is the **"Оценить упражнение" trigger button** (`span.button-content`) plus the
hint text **"Это упражнение с ручной проверкой, оцени…"**. The old code keyed
`has_grade_button` off the estimate-view, so it classified every ungraded exercise as
auto-checked and graded nothing. Fixed in `scraper/lesson.py`:
`has_grade_button = block has GRADE_EXERCISE_BTN AND not is_graded`;
`is_graded` comes from a parseable "N/M" inside an estimate-view.

**Lesson player rendering.** Direct navigation to a `/lesson/{id}` URL leaves the SPA
stuck on **"Загрузка марафона"** with `0 из 0 уроков`. The player only renders fully
when reached via marathon → student → **Прогресс ученика** → **Открыть урок**, and even
then needs **~6–8 s** plus a gate on `.sections-list_item` existing AND the loading text
being gone (`lesson.wait_lesson_ready`). The "Открыть урок" click triggers an **async SPA
navigation** — `page.url` stays on the students page for a moment, so `open_lesson` now
`wait_for_url("/lesson/")` before parsing ids.

**Sections.** Exercises are split across sections reached via `?section=n` (left rail
`.sections-list_item`; the trailing item is "Завершить урок"). On L18 the ungraded
exercises were in sections 0, 1 and 4 — so the runner now walks **every** section
(`gather_exercises`) and navigates back to an exercise's section before grading it.
The composite idempotency key includes the section index: `f"{lesson_id}:s{n}:{number}"`.

**Grade modal — CONFIRMED (`# CONFIRM-LIVE` markers removed).**
- Container `.tir-modal`, title "Поставить оценку".
- Score: `.tir-modal input[type=number]` (defaults to "5"). **Max score = 5**
  ("Максимальное количество баллов: 5") → `selectors.SCORE_MAX`.
- Comment: hidden behind a **toggle switch** (`.tir-toggle`, label "Добавить
  комментарий"). Flip it on → reveals `.tir-modal textarea` (placeholder
  "Ваш комментарий…"). The poster toggles before filling.
- Submit: blue `.tir-modal button.blue:has-text('Продолжить')`; cancel = gray "Отмена".

**Safety:** entire capture was read-only — modal opened then Escaped, no score posted,
no lesson completed.

### R0.3 — Answer extraction, per-exercise max, graded-state timing (2026-06-18)

Found while validating a real (since-removed) test grade. Three corrections:

- **Student answer ≠ block instructions.** `block.inner_text()` is the TASK PROMPT.
  The student's WRITTEN answer lives in a `contenteditable.html-editor-inline`
  (`selectors.ANSWER_EDITOR`). Confirmed live: Akerke L15 #1.3 editor holds her
  rewritten sentences; Nurdana L18 #1.2 editor is empty (she never did it). The bot
  had been grading the instructions, which (a) produced garbage evaluations and
  (b) hid empty submissions from the empty-answer guard → it graded blank work.
  Fix: `lesson._read_written_answer` reads the editor; empty → None → flagged.
  Audio answers are unchanged (`audio_url`).
- **score_max is PER-EXERCISE.** Nurdana L18 #1.2 is /6; the audio exercise modal
  was /5. The only authoritative source is the grade modal text "Максимальное
  количество баллов: N". Fix: the grade flow now opens the modal FIRST, reads the
  max (`poster.parse_modal_max`), evaluates against it, then submits.
- **`.exercise-estimate-view` render lag.** When walking sections quickly, a graded
  exercise can momentarily report ungraded (its estimate-view has not rendered).
  Fix: `goto_section` waits for networkidle + a settle, and `runner` re-checks
  `poster.is_already_graded` on the settled section before grading (defense in depth).

**Still unverified live:** an end-to-end real grade submission with the corrected
flow (answer from editor + per-exercise max). The earlier one-off submit proved the
modal mechanics; the corrected pipeline has not yet posted a real grade.

# Edvibe Grader — UI design prompt

Paste-ready prompt for an AI UI generator (v0 / Lovable / Figma Make) or as a brief for
implementing the frontend. Companion to `2026-06-16-edvibe-grader-design.md` (§7).

---

```text
Design a local, single-user web application called "Edvibe Grader" — an
operator dashboard a private English teacher uses to run and supervise an
automated homework-grading bot for the edvibe.com platform.

TARGET OUTPUT
React + TypeScript + Tailwind CSS + shadcn/ui components. Desktop-first
(min 1280px), responsive down to a laptop. Light and dark themes.

PRODUCT CONTEXT
The bot logs into edvibe.com, finds students whose homework is in "Awaiting"
status, evaluates each exercise with AI (audio answers are transcribed and
scored; written answers are scored), and posts a score out of 10 plus a short
English comment, then marks the lesson complete. This UI lets the teacher
start runs, watch them live, review/override the AI's proposed grades, and
audit everything. The actions are irreversible, so the UI must feel
trustworthy, calm, and precise — never flashy. Think "flight-deck for grading":
dense data, clear status, obvious safety affordances.

BRAND & VISUAL SYSTEM
- Tone: professional EdTech ops tool. Trustworthy, modern, restrained.
- Primary accent: indigo/violet (education + focus). Neutral grays for surface.
- Status semantics (use consistently everywhere):
    evaluating = blue, graded/done = green, skipped = gray,
    flagged/needs-review = amber, error = red, dry-run = dashed/striped purple.
- Typography: Inter. Numeric scores in a tabular, slightly larger weight.
- Density: compact data tables, generous cards on the dashboard.
- Components: left sidebar nav, top bar with a persistent RUN STATUS pill
  (Idle / Running · 12/43 students / Dry-run / Error). Rounded-xl cards,
  subtle borders, soft shadows. shadcn Table, Badge, Dialog, Tabs, Sheet,
  Progress, Toast, Command palette.

GLOBAL LAYOUT
- Left sidebar: Dashboard, New Run, Live Monitor, Review Queue, Students,
  History, Flagged, Settings. Collapsible. Active state highlighted.
- Top bar: app name + environment ("Localhost"), theme toggle, the global
  RUN STATUS pill (clickable → Live Monitor), and a small lock icon noting
  "credentials stored locally".

SCREENS

1) DASHBOARD
   - Row of stat cards: "Students with pending work" (e.g. 17 of 43),
     "Lessons awaiting" (e.g. 41), "Last run" (status + timestamp),
     "Flagged for review" (e.g. 5, amber).
   - Big primary "Start a run" button.
   - "Recent runs" list: each row = mode badge (Dry-run / Full-auto / Review),
     started-at, duration, counts (graded / skipped / flagged / errors),
     status. Click → History detail.
   - An advisory banner slot for warnings (e.g. "1 lesson was completed by a
     previous run — review in Reconcile").

2) NEW RUN (form, can be a centered card or a Sheet)
   - Mode selector (segmented control): Dry-run (safe, submits nothing) ·
     Full-auto (grades AND completes) · Review-queue (drafts, you approve).
     Each option has a one-line description; Full-auto shows an amber caution.
   - Scope: "All of Mr. Adilet's Pre-IELTS students" toggle, OR a searchable
     multi-select student picker.
   - Safety caps: max students (number), max lessons per student (number),
     "Run browser visibly (headed)" switch.
   - Confidence threshold slider (below this, the bot flags instead of grading).
   - Footer: a prominent confirm button whose label reflects the mode —
     "Start Dry-run" (neutral) vs "Start Full-auto run" (amber, with a
     confirm dialog: 'This will submit real grades and complete lessons.').

3) LIVE MONITOR
   - Left: a live tree — Student ▸ Lesson ▸ Exercise, with status chips and
     progress. Current item highlighted, auto-scrolling.
   - Right top: progress summary (X/Y students, ETA, mode pill, Stop button —
     red, with confirm).
   - Right bottom: a streaming log console (monospace, autoscroll, filterable
     by level). Error rows expandable to show a screenshot thumbnail.
   - Per-exercise card on hover/select: type (audio/text), the transcript or
     answer, the AI's proposed score + comment, confidence, and what action
     was taken (graded / skipped: already auto-checked / flagged / error).

4) REVIEW QUEUE
   - Filter bar: by student, lesson, status, exercise type, confidence.
   - Table or card grid of proposed grades. Each item shows:
       student name, Russian lesson name + section, exercise number (e.g. 1.2),
       type icon (audio / text), an inline audio player WITH the transcript
       for audio items (or the written answer for text), the AI score in an
       editable 0–10 stepper, the English comment in an editable textarea,
       a confidence meter, and Approve / Reject buttons.
   - Bulk actions: select-all, "Approve selected", "Approve all high-confidence".
   - A sticky summary footer: "12 approved · 3 edited · 2 rejected · Submit 12".

5) STUDENTS
   - Table of the 43 students with: name, # awaiting lessons, last activity,
     curator. Expand a row to list that student's awaiting lessons with status.
   - Row action: "Run for this student".

6) HISTORY / AUDIT
   - Filterable list of runs. Detail view = full timeline: every exercise,
     proposed score vs submitted score, dry-run flag, timestamps, and whether
     a human edited it. Export.
   - A "Reconcile" tab: read-only view of what is currently marked complete on
     the platform, highlighting anything the bot completed — so leftovers
     (e.g. a lesson completed unexpectedly for a student) are easy to spot.

7) FLAGGED
   - Cards for items the bot refused to auto-grade: reason (audio download
     failed / low confidence / selector not found / OpenAI error), the context,
     and a "Resolve manually" link plus "Retry".

8) SETTINGS
   - Sections: Credentials (Edvibe login + password, OpenAI API key — masked,
     with a "stored locally only" note), Models (transcription + evaluation
     model names), Grading (score scale, confidence threshold, rubric notes),
     Behavior (default mode = Dry-run, pacing/delay, headed default,
     marathon = "Pre-IELTS", curator = "Mister Adilet"), Danger zone.

CROSS-CUTTING STATES (design all of these)
- Empty states (no runs yet, empty queue, no flagged items) with friendly
  guidance.
- Loading / skeletons for tables and the live tree.
- Error toasts and inline error rows.
- A persistent, unmissable visual difference between DRY-RUN (safe, dashed
  purple accents, "nothing was submitted" banners) and LIVE FULL-AUTO
  (solid, amber caution accents, confirmation dialogs).
- Accessibility: keyboard nav, focus rings, sufficient contrast in both themes.

SAMPLE DATA TO RENDER REALISTIC SCREENS
- Marathon: "Pre-IELTS", Curator: "Mister Adilet", 43 students.
- Student names (mix Latin + Cyrillic): "Анель", "Dias", "Аружан", "Timur".
- Lesson names: "Lesson 14 — Entertainment", sections "Entertainment
  discussion", "Grammar", "Vocabulary", "Reading time.", "Shadowing".
- Exercise examples: "1.2 Audio answer (00:00 / 02:04)", "2.1 Gap-fill
  (auto-checked)", "Shadowing 3.1 (audio)".
- Proposed grade example: score 7/10, comment "Good task response and clear
  pronunciation; watch past-tense endings and link your ideas with connectors."
- Confidence values 0.62–0.95; one flagged item: "Audio download failed".

Deliver a cohesive, polished, real-feeling product — not a wireframe.
```

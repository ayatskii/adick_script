"""Verbatim sample data ported from web/src/data.ts.

Returned by the data endpoints as an empty-store fallback so the UI is
populated immediately (before any real run writes to the SQLite store). Keep
the field names and values identical to the frontend so shapes round-trip.
"""

from __future__ import annotations

# ============================================================
# Run history rows (RUN_ROWS) — Dashboard "Recent runs" + History.
# The frontend's RunRow is display-oriented; the contract's Run shape is
# normalized. We expose runs in the normalized Run shape, but keep the
# original RunRow values reachable for the History "runs" display via
# SEED_RUN_ROWS.
# ============================================================
SEED_RUN_ROWS = [
    {
        "id": "h1",
        "modeBadgeStatus": "dryrun",
        "modeBadgeLabel": "Dry-run",
        "started": "Today 09:14",
        "duration": "2m 41s",
        "counts": "14 ✓ · 3 skip · 1 ⚑",
        "statusBadgeStatus": "graded",
        "statusBadgeLabel": "Success",
    },
    {
        "id": "h2",
        "modeBadgeStatus": "flagged",
        "modeBadgeLabel": "Full-auto",
        "started": "Yesterday 18:02",
        "duration": "11m 06s",
        "counts": "38 ✓ · 5 skip · 2 ⚑",
        "statusBadgeStatus": "graded",
        "statusBadgeLabel": "Success",
    },
    {
        "id": "h3",
        "modeBadgeStatus": "queued",
        "modeBadgeLabel": "Review",
        "started": "Yesterday 12:30",
        "duration": "4m 12s",
        "counts": "12 draft · 2 ⚑",
        "statusBadgeStatus": "flagged",
        "statusBadgeLabel": "2 flagged",
    },
    {
        "id": "h4",
        "modeBadgeStatus": "flagged",
        "modeBadgeLabel": "Full-auto",
        "started": "Mon 20:48",
        "duration": "9m 33s",
        "counts": "31 ✓ · 1 ✗",
        "statusBadgeStatus": "error",
        "statusBadgeLabel": "1 error",
    },
    {
        "id": "h5",
        "modeBadgeStatus": "dryrun",
        "modeBadgeLabel": "Dry-run",
        "started": "Mon 16:10",
        "duration": "1m 58s",
        "counts": "9 ✓ · 2 skip",
        "statusBadgeStatus": "graded",
        "statusBadgeLabel": "Success",
    },
]

# Normalized Run shape (contract §Data shapes) derived from the seed rows, so
# GET /api/runs returns the contract shape even on an empty store.
SEED_RUNS = [
    {
        "id": "h1",
        "mode": "dry_run",
        "started_at": "Today 09:14",
        "finished_at": "Today 09:16",
        "status": "graded",
        "duration": "2m 41s",
        "counts": {"graded": 14, "skipped": 3, "flagged": 1, "errors": 0, "completed_lessons": 0},
    },
    {
        "id": "h2",
        "mode": "full_auto",
        "started_at": "Yesterday 18:02",
        "finished_at": "Yesterday 18:13",
        "status": "graded",
        "duration": "11m 06s",
        "counts": {"graded": 38, "skipped": 5, "flagged": 2, "errors": 0, "completed_lessons": 0},
    },
    {
        "id": "h3",
        "mode": "review",
        "started_at": "Yesterday 12:30",
        "finished_at": "Yesterday 12:34",
        "status": "flagged",
        "duration": "4m 12s",
        "counts": {"graded": 12, "skipped": 0, "flagged": 2, "errors": 0, "completed_lessons": 0},
    },
    {
        "id": "h4",
        "mode": "full_auto",
        "started_at": "Mon 20:48",
        "finished_at": "Mon 20:57",
        "status": "error",
        "duration": "9m 33s",
        "counts": {"graded": 31, "skipped": 0, "flagged": 0, "errors": 1, "completed_lessons": 0},
    },
    {
        "id": "h5",
        "mode": "dry_run",
        "started_at": "Mon 16:10",
        "finished_at": "Mon 16:12",
        "status": "graded",
        "duration": "1m 58s",
        "counts": {"graded": 9, "skipped": 2, "flagged": 0, "errors": 0, "completed_lessons": 0},
    },
]

# ============================================================
# Review queue items (REVIEW_ITEMS) — 6 items verbatim.
# ============================================================
SEED_REVIEW_ITEMS = [
    {
        "id": "r1",
        "student": "Анель",
        "lesson": "Lesson 14 — Entertainment",
        "section": "Entertainment discussion",
        "ex": "1.2",
        "type": "audio",
        "duration": "02:04",
        "score": 7,
        "conf": 0.84,
        "transcript": "In my free time I like watching the series and listen to podcasts about science. Last weekend I have watched a documentary about ocean, it was really interesting and I learn many new words…",
        "comment": "Good task response and clear pronunciation; watch past-tense endings and link your ideas with connectors.",
        "status": "pending",
        "edited": False,
    },
    {
        "id": "r2",
        "student": "Dias",
        "lesson": "Lesson 14 — Entertainment",
        "section": "Grammar",
        "ex": "2.1",
        "type": "text",
        "score": 9,
        "conf": 0.91,
        "transcript": "If I _had_ more time, I _would learn_ to play the guitar. She _has been_ working here since 2019.",
        "comment": "Excellent — all conditional and perfect forms correct. Minor: spacing around blanks.",
        "status": "pending",
        "edited": False,
    },
    {
        "id": "r3",
        "student": "Аружан",
        "lesson": "Lesson 12 — Travel",
        "section": "Vocabulary",
        "ex": "3.4",
        "type": "text",
        "score": 6,
        "conf": 0.66,
        "transcript": "destination, itinerary, sightseeing, accomodation, departure",
        "comment": "Most words used correctly. Spelling: \"accomodation\" → \"accommodation\". Add example sentences next time.",
        "status": "pending",
        "edited": False,
    },
    {
        "id": "r4",
        "student": "Timur",
        "lesson": "Lesson 14 — Entertainment",
        "section": "Shadowing",
        "ex": "3.1",
        "type": "audio",
        "duration": "01:12",
        "score": 8,
        "conf": 0.88,
        "transcript": "The film industry has changed dramatically over the past decade, with streaming platforms…",
        "comment": "Strong rhythm and intonation. A couple of dropped word-endings — keep it up!",
        "status": "pending",
        "edited": False,
    },
    {
        "id": "r5",
        "student": "Нурайым",
        "lesson": "Lesson 13 — Health",
        "section": "Reading time.",
        "ex": "1.1",
        "type": "text",
        "score": 5,
        "conf": 0.62,
        "transcript": "The passage is about how sleep affect our memory and the writer think teenagers need more sleep.",
        "comment": "Main idea captured but several grammar slips (affect/affects, think/thinks). Re-read for subject–verb agreement.",
        "status": "pending",
        "edited": False,
    },
    {
        "id": "r6",
        "student": "Madina",
        "lesson": "Lesson 14 — Entertainment",
        "section": "Entertainment discussion",
        "ex": "1.3",
        "type": "audio",
        "duration": "01:48",
        "score": 9,
        "conf": 0.95,
        "transcript": "I think social media changed how we consume entertainment completely. We can discover new artists instantly…",
        "comment": "Fluent, well-organised and natural. Great use of linking phrases.",
        "status": "pending",
        "edited": False,
    },
]

# ============================================================
# Student roster (STUDENT_ROWS) — 12 rows verbatim.
# ============================================================
SEED_STUDENTS = [
    {
        "id": "s1",
        "name": "Анель",
        "awaiting": 3,
        "lastActivity": "2h ago",
        "lessons": [
            {"name": "Lesson 14 — Entertainment", "status": "queued"},
            {"name": "Lesson 13 — Health", "status": "queued"},
            {"name": "Lesson 12 — Travel", "status": "flagged"},
        ],
    },
    {
        "id": "s2",
        "name": "Dias",
        "awaiting": 2,
        "lastActivity": "4h ago",
        "lessons": [
            {"name": "Lesson 14 — Entertainment", "status": "queued"},
            {"name": "Lesson 13 — Health", "status": "queued"},
        ],
    },
    {
        "id": "s3",
        "name": "Аружан",
        "awaiting": 4,
        "lastActivity": "1d ago",
        "lessons": [
            {"name": "Lesson 12 — Travel", "status": "flagged"},
            {"name": "Lesson 13 — Health", "status": "queued"},
            {"name": "Lesson 14 — Entertainment", "status": "queued"},
            {"name": "Lesson 11 — Work", "status": "queued"},
        ],
    },
    {
        "id": "s4",
        "name": "Timur",
        "awaiting": 1,
        "lastActivity": "6h ago",
        "lessons": [
            {"name": "Lesson 14 — Entertainment", "status": "error"},
        ],
    },
    {
        "id": "s5",
        "name": "Нурайым",
        "awaiting": 3,
        "lastActivity": "3h ago",
        "lessons": [
            {"name": "Lesson 13 — Health", "status": "queued"},
            {"name": "Lesson 12 — Travel", "status": "queued"},
            {"name": "Lesson 14 — Entertainment", "status": "queued"},
        ],
    },
    {
        "id": "s6",
        "name": "Madina",
        "awaiting": 1,
        "lastActivity": "30m ago",
        "lessons": [
            {"name": "Lesson 14 — Entertainment", "status": "queued"},
        ],
    },
    {
        "id": "s7",
        "name": "Ерлан",
        "awaiting": 2,
        "lastActivity": "1d ago",
        "lessons": [
            {"name": "Lesson 13 — Health", "status": "queued"},
            {"name": "Lesson 12 — Travel", "status": "queued"},
        ],
    },
    {
        "id": "s8",
        "name": "Алишер",
        "awaiting": 0,
        "lastActivity": "5d ago",
        "lessons": [],
    },
    {
        "id": "s9",
        "name": "Camila",
        "awaiting": 2,
        "lastActivity": "8h ago",
        "lessons": [
            {"name": "Lesson 14 — Entertainment", "status": "queued"},
            {"name": "Lesson 11 — Work", "status": "queued"},
        ],
    },
    {
        "id": "s10",
        "name": "Бекзат",
        "awaiting": 3,
        "lastActivity": "2d ago",
        "lessons": [
            {"name": "Lesson 12 — Travel", "status": "queued"},
            {"name": "Lesson 13 — Health", "status": "queued"},
            {"name": "Lesson 14 — Entertainment", "status": "queued"},
        ],
    },
    {
        "id": "s11",
        "name": "Aizhan",
        "awaiting": 1,
        "lastActivity": "12h ago",
        "lessons": [
            {"name": "Lesson 13 — Health", "status": "queued"},
        ],
    },
    {
        "id": "s12",
        "name": "Daniyar",
        "awaiting": 0,
        "lastActivity": "1w ago",
        "lessons": [],
    },
]

# ============================================================
# History timeline entries (TIMELINE_ENTRIES) — 6 entries verbatim.
# ============================================================
SEED_TIMELINE = [
    {"student": "Анель", "ex": "1.2", "proposedScore": 7, "submittedScore": 7, "status": "graded", "humanEdited": False, "tsOffset": 0},
    {"student": "Анель", "ex": "2.1", "proposedScore": None, "submittedScore": None, "status": "skipped", "humanEdited": False, "tsOffset": 45},
    {"student": "Dias", "ex": "1.2", "proposedScore": 6, "submittedScore": 7, "status": "graded", "humanEdited": True, "tsOffset": 90},
    {"student": "Dias", "ex": "2.1", "proposedScore": 9, "submittedScore": 9, "status": "graded", "humanEdited": False, "tsOffset": 135},
    {"student": "Аружан", "ex": "3.4", "proposedScore": None, "submittedScore": None, "status": "flagged", "humanEdited": False, "tsOffset": 180},
    {"student": "Timur", "ex": "3.1", "proposedScore": None, "submittedScore": None, "status": "error", "humanEdited": False, "tsOffset": 225},
]

# ============================================================
# Reconcile rows (RECONCILE_ROWS) — 4 rows verbatim.
# ============================================================
SEED_RECONCILE = [
    {"student": "Анель", "lesson": "Lesson 14 — Entertainment", "completedBy": "This bot · today 09:14", "flagStatus": None, "flagLabel": None},
    {"student": "Dias", "lesson": "Lesson 14 — Entertainment", "completedBy": "This bot · today 09:15", "flagStatus": None, "flagLabel": None},
    {"student": "Нурайым", "lesson": "Lesson 13 — Health", "completedBy": "Previous run · yesterday", "flagStatus": "flagged", "flagLabel": "Leftover — check"},
    {"student": "Madina", "lesson": "Lesson 12 — Travel", "completedBy": "Manually completed", "flagStatus": None, "flagLabel": None},
]

# ============================================================
# Flagged items (FLAGGED_ITEMS) — 5 cards verbatim.
# ============================================================
SEED_FLAGGED = [
    {
        "id": "f1",
        "student": "Аружан",
        "lesson": "Lesson 12 — Travel",
        "ex": "3.4",
        "reason": "Low confidence",
        "severity": "Needs a look",
        "detail": "Confidence 0.61 — below your 0.70 threshold. The answer mixes correct and misspelled vocabulary, so the bot held off.",
    },
    {
        "id": "f2",
        "student": "Timur",
        "lesson": "Lesson 14 — Entertainment",
        "ex": "3.1",
        "reason": "Audio download failed",
        "severity": "Blocked",
        "detail": "The shadowing audio returned 403 from the Edvibe CDN after 3 retries. No transcript could be produced.",
    },
    {
        "id": "f3",
        "student": "Dias",
        "lesson": "Lesson 14 — Entertainment",
        "ex": "2.2",
        "reason": "Selector not found",
        "severity": "Blocked",
        "detail": "The score input field did not appear within 15s. The lesson page layout may have changed.",
    },
    {
        "id": "f4",
        "student": "Madina",
        "lesson": "Lesson 13 — Health",
        "ex": "1.4",
        "reason": "OpenAI error",
        "severity": "Transient",
        "detail": "Rate limit (429) hit during evaluation. The item will retry automatically on the next run.",
    },
    {
        "id": "f5",
        "student": "Нурайым",
        "lesson": "Lesson 12 — Travel",
        "ex": "2.1",
        "reason": "Low confidence",
        "severity": "Needs a look",
        "detail": "Confidence 0.64 — the answer drifts partly off-topic, so a human should score it.",
    },
]

# Empty by default; the seed history runs carry no audit rows.
SEED_AUDIT: list[dict] = []

# ============================================================
# Settings defaults (SETTINGS_DEFAULTS) — non-secret subset surfaced by the
# API. Credentials are masked.
# ============================================================
SEED_SETTINGS = {
    "edvibeLogin": "mr.adilet@edvibe.com",
    "edvibePassword": "••••••••",
    "openaiApiKey": "sk-••••••••",
    "transcriptionModel": "whisper-1",
    "evaluationModel": "gpt-4o",
    "scoreScale": "0 – 10",
    "confidenceThreshold": 0.70,
    "rubricNotes": "Reward task response & coherence; be gentle on minor grammar.",
    "defaultMode": "Dry-run",
    "pacingDelayMs": 900,
    "marathon": "Pre-IELTS",
    "curator": "Mister Adilet",
}

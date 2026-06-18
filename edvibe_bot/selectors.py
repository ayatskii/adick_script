# edvibe_bot/selectors.py — SINGLE SOURCE OF TRUTH for edvibe.com selectors.
# Values confirmed live in Phase 0 (docs/superpowers/specs/phase0-exploration-notes.md).
# edvibe is a Vue SPA: NO data-testid, NO id attributes. Identity comes from
# URLs + visible text. Selectors are semantic BEM classes or Playwright text=.
# Do NOT redefine these elsewhere.

import re

# Login / URLs (confirmed)
LOGIN_URL = "https://edvibe.com/login"
AUTHED_URL = "https://edvibe.com/cabinet/school/classes"
NAV_CLASSES = "https://edvibe.com/cabinet/school/classes"   # open_marathon goto target
LOGIN_EMAIL = "input[type=email]"
LOGIN_PASSWORD = "input[placeholder='Password']"
LOGIN_SUBMIT = "button:has-text('Log in to your account')"

# Marathon nav + curator filter (confirmed)
MARATHONS_TAB = "text=Марафоны"
PRE_IELTS_CARD = "text=Pre-IELTS"
FILTER_BUTTON = "text=Фильтр"
CURATOR_OPTION = "text=Mister Adilet"        # curator pick inside "Кураторы"
FILTER_APPLY = "button:has-text('Применить')"

# Students (id + name + email are TEXT; no attributes). The roster is a VIRTUALISED
# list — rows lazy-render on scroll, so list_students scrolls and accumulates.
STUDENT_ROW = ".avatar-li"                     # one card per student (was .marathon-student-li, stale)
STUDENT_SEARCH = "input[placeholder='Поиск учеников']"  # filter box (search by email is unique)
STUDENT_PROGRESS_BTN = "text=Прогресс ученика"
# student id = 7-digit numeric text in the row (e.g. "3176678"); see STUDENT_ID_RE.
STUDENT_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")

# Progress modal + lessons (confirmed)
PROGRESS_MODAL = ".marathon-student-progress-modal"
PROGRESS_MODAL_CLOSE = ".marathon-student-progress-modal .icon.close"
LESSON_ROW = ".marathon-modules-lessons-lesson-li"
LESSON_OPEN_BUTTON = "text=Открыть урок"
# lesson name = LESSON_ROW innerText first line ("Lesson 14: Entertainment").

# Lesson view (confirmed live on Nurdana L18, 2026-06-16)
# The marathon lesson player needs ~6-8s to render; gate on SECTION_ITEM existing
# AND the "Загрузка марафона" loading text being gone before scraping.
LESSON_LAYOUT = ".lesson-layout.marathon-lesson-layout"
LESSON_LOADING_TEXT = "Загрузка марафона"     # present while the SPA player loads
SECTION_ITEM = ".sections-list_item"          # left-rail section switcher rows
EXERCISE_BLOCK = ".exercise-wrapper"
EXERCISE_AUDIO = "audio"                      # read .currentSrc
# The student's WRITTEN answer lives in this contenteditable rich-text editor —
# NOT in the block's innerText (which is the task instructions). Confirmed live:
# completed writing exercise → editor holds the rewritten sentences; an unanswered
# exercise → editor is empty (so we must flag empty, never grade the instructions).
ANSWER_EDITOR = ".html-editor-inline"
COMPLETE_LESSON_BTN = "text=Завершить урок"   # a .sections-list_item div, NOT a <button>
# section switch: CLICK the nth SECTION_ITEM (0-indexed). The ?section=n URL param
# does NOT work — the SPA canonicalises it back to section 0.

# --- Ungraded-exercise detection (confirmed) ---
# IMPORTANT: `.exercise-estimate-view` exists ONLY for ALREADY-GRADED exercises
# (it renders the awarded score). UNGRADED manual-check exercises do NOT have it.
# The real "awaiting grading" marker is the "Оценить упражнение" trigger button,
# accompanied by the description "Это упражнение с ручной проверкой, оцени...".
GRADE_ESTIMATE_VIEW = ".exercise-estimate-view"   # graded-only score widget
GRADE_EXERCISE_BTN = "text=Оценить упражнение"     # span.button-content; click → opens grade modal
MANUAL_CHECK_HINT = "Это упражнение с ручной проверкой"  # ungraded manual-check marker text

# --- Grade modal (CONFIRMED live, read-only Phase 0 capture) ---
# Opened by clicking GRADE_EXERCISE_BTN. Vue-rendered container `.tir-modal`,
# title "Поставить оценку", form `.exercise-estimate-form`.
GRADE_MODAL = ".tir-modal"
GRADE_MODAL_TITLE = "Поставить оценку"
SCORE_MAX = 5                                    # "Максимальное количество баллов: 5"
# Absolute (page-scoped) forms:
SCORE_INPUT = ".tir-modal input[type=number]"   # default value "5"
COMMENT_TOGGLE = ".tir-modal .exercise-estimate-form .tir-toggle"  # reveals the comment field
COMMENT_INPUT = ".tir-modal textarea"           # placeholder "Ваш комментарий..."
GRADE_SAVE_BTN = ".tir-modal button.blue:has-text('Продолжить')"  # blue submit; "Отмена" = cancel
GRADE_CANCEL_BTN = ".tir-modal button.gray:has-text('Отмена')"
# Modal-RELATIVE forms (used after scoping a locator to GRADE_MODAL):
SCORE_INPUT_REL = "input[type=number]"
COMMENT_TOGGLE_REL = ".exercise-estimate-form .tir-toggle"
COMMENT_INPUT_REL = "textarea"
GRADE_SAVE_BTN_REL = "button.blue:has-text('Продолжить')"
GRADE_CANCEL_BTN_REL = "button.gray:has-text('Отмена')"
# The modal states the real per-exercise maximum, e.g. "Максимальное количество
# баллов: 6". This is the authoritative score_max (it varies per exercise).
MODAL_MAX_LABEL = "Максимальное количество баллов"

# URL / text patterns (identity source — replaces the dropped *_ID_ATTR).
LESSON_URL_RE = re.compile(r"/marathon/\d+/lesson/(\d+)")   # group(1) = lessonId
PUPIL_QS = "pupil"                             # ?pupil={studentId}
STUDENT_ID_RE = re.compile(r"\d{4,}")          # numeric student id in the row text

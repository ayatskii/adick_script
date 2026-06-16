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

# Students (id + name are TEXT; no attributes)
STUDENT_ROW = ".marathon-student-li"
STUDENT_PROGRESS_BTN = "text=Прогресс ученика"
# student id = numeric text in the row (e.g. "3176678"); see STUDENT_ID_RE.

# Progress modal + lessons (confirmed)
PROGRESS_MODAL = ".marathon-student-progress-modal"
PROGRESS_MODAL_CLOSE = ".marathon-student-progress-modal .icon.close"
LESSON_ROW = ".marathon-modules-lessons-lesson-li"
LESSON_OPEN_BUTTON = "text=Открыть урок"
# lesson name = LESSON_ROW innerText first line ("Lesson 14: Entertainment").

# Lesson view (confirmed)
LESSON_LAYOUT = ".lesson-layout.marathon-lesson-layout"
EXERCISE_BLOCK = ".exercise-wrapper"
EXERCISE_AUDIO = "audio"                      # read .currentSrc
GRADE_ESTIMATE_VIEW = ".exercise-estimate-view"
GRADE_EXERCISE_BTN = "text=Оценить упражнение"   # a DIV, not a <button>
COMPLETE_LESSON_BTN = "text=Завершить урок"      # a DIV, not a <button>
# section switch: append ?section=n to the lesson URL (0-indexed).

# Grade modal (best-guess — only reachable on a live ungraded exercise;
# the dry-run path never clicks these, so unconfirmed is safe).
SCORE_INPUT = "input[type=number]"            # CONFIRM-LIVE
COMMENT_INPUT = "textarea"                     # CONFIRM-LIVE
GRADE_SAVE_BTN = "text=Продолжить"             # CONFIRM-LIVE

# URL / text patterns (identity source — replaces the dropped *_ID_ATTR).
LESSON_URL_RE = re.compile(r"/marathon/\d+/lesson/(\d+)")   # group(1) = lessonId
PUPIL_QS = "pupil"                             # ?pupil={studentId}
STUDENT_ID_RE = re.compile(r"\d{4,}")          # numeric student id in the row text

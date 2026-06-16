# edvibe_bot/selectors.py — SINGLE SOURCE OF TRUTH for edvibe.com selectors.
# Values are best-guess defaults, CONFIRMED/updated in Phase 0. Do NOT redefine elsewhere.

# URLs
LOGIN_URL = "https://edvibe.com/login"                      # CONFIRM
AUTHED_URL = "https://edvibe.com/cabinet/school/classes"    # CONFIRM

# Login
LOGIN_EMAIL = "input[type=email]"                           # CONFIRM
LOGIN_PASSWORD = "input[type=password]"                     # CONFIRM
LOGIN_SUBMIT = "button[type=submit]"                        # CONFIRM

# Marathon dashboard + curator filter
NAV_CLASSES = "https://edvibe.com/cabinet/school/classes"   # CONFIRM (classes landing; open_marathon goto target)
MARATHONS_TAB = "text=Марафоны"
PRE_IELTS_CARD = "text=Pre-IELTS"
FILTER_BUTTON = "text=Фильтр"
CURATOR_OPTION = "text=Mister Adilet"
FILTER_APPLY = "text=Применить"

# Students
STUDENT_ROW = "[data-testid=student-row]"                   # CONFIRM
STUDENT_ID_ATTR = "data-student-id"                         # CONFIRM
STUDENT_NAME = "[data-testid=student-name]"                 # CONFIRM
STUDENT_PROGRESS_BTN = "text=Прогресс ученика"

# Progress modal — lessons
LESSON_ROW = "[data-testid=lesson-row]"                     # CONFIRM
LESSON_ID_ATTR = "data-lesson-id"                           # CONFIRM
LESSON_NAME = "[data-testid=lesson-name]"                   # CONFIRM
LESSON_STATUS_AWAITING = ".status--awaiting"                # CONFIRM
LESSON_OPEN_BUTTON = "text=Открыть урок"

# Lesson view — sections + exercises
SECTION_NAV = "[data-testid=section]"                       # CONFIRM
EXERCISE_BLOCK = "[data-testid=exercise]"                   # CONFIRM
EXERCISE_ID_ATTR = "data-exercise-id"                       # CONFIRM (stable per-exercise id -> ledger key)
EXERCISE_NUMBER = "[data-testid=exercise-number]"           # CONFIRM
EXERCISE_PROMPT = "[data-testid=exercise-prompt]"           # CONFIRM
EXERCISE_AUDIO = "audio"                                    # CONFIRM
EXERCISE_TEXT_ANSWER = "[data-testid=text-answer]"          # CONFIRM
GRADE_EXERCISE_BTN = "text=Оценить упражнение"

# Grade modal
SCORE_INPUT = "input[type=number]"                          # CONFIRM
COMMENT_INPUT = "textarea"                                  # CONFIRM
GRADE_SAVE_BTN = "text=Продолжить"

# Lesson completion
COMPLETE_LESSON_BTN = "text=Завершить урок"

from edvibe_bot import selectors
from edvibe_bot.errors import SelectorError

REQUIRED = [
    "LOGIN_URL", "AUTHED_URL", "LOGIN_EMAIL", "LOGIN_PASSWORD", "LOGIN_SUBMIT",
    "NAV_CLASSES", "MARATHONS_TAB", "PRE_IELTS_CARD", "FILTER_BUTTON", "CURATOR_OPTION", "FILTER_APPLY",
    "STUDENT_ROW", "STUDENT_ID_ATTR", "STUDENT_NAME", "STUDENT_PROGRESS_BTN",
    "LESSON_ROW", "LESSON_ID_ATTR", "LESSON_NAME", "LESSON_STATUS_AWAITING", "LESSON_OPEN_BUTTON",
    "SECTION_NAV", "EXERCISE_BLOCK", "EXERCISE_ID_ATTR", "EXERCISE_NUMBER", "EXERCISE_PROMPT",
    "EXERCISE_AUDIO", "EXERCISE_TEXT_ANSWER", "GRADE_EXERCISE_BTN",
    "SCORE_INPUT", "COMMENT_INPUT", "GRADE_SAVE_BTN", "COMPLETE_LESSON_BTN",
]

def test_all_required_selectors_present():
    for name in REQUIRED:
        value = getattr(selectors, name)
        assert isinstance(value, str) and value

def test_selector_error_is_exception():
    assert issubclass(SelectorError, Exception)

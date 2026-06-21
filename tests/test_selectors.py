from edvibe_bot import selectors
from edvibe_bot.errors import SelectorError

REQUIRED = [
    "LOGIN_URL", "AUTHED_URL", "NAV_CLASSES", "LOGIN_EMAIL", "LOGIN_PASSWORD", "LOGIN_SUBMIT",
    "MARATHONS_TAB", "PRE_IELTS_CARD", "FILTER_BUTTON", "CURATOR_DROPDOWN", "FILTER_APPLY",
    "STUDENT_ROW", "STUDENT_PROGRESS_BTN",
    "PROGRESS_MODAL", "PROGRESS_MODAL_CLOSE", "LESSON_ROW", "LESSON_OPEN_BUTTON",
    "LESSON_LAYOUT", "EXERCISE_BLOCK", "EXERCISE_AUDIO",
    "GRADE_ESTIMATE_VIEW", "GRADE_EXERCISE_BTN", "COMPLETE_LESSON_BTN",
    "SCORE_INPUT", "COMMENT_INPUT", "GRADE_SAVE_BTN", "PUPIL_QS",
]

# Attributes that the old (data-testid) strategy assumed but which DON'T exist
# on the live DOM — they must be gone now.
REMOVED = ["STUDENT_ID_ATTR", "LESSON_ID_ATTR", "EXERCISE_ID_ATTR",
           "LESSON_STATUS_AWAITING", "SECTION_NAV"]


def test_all_required_selectors_present():
    for name in REQUIRED:
        value = getattr(selectors, name)
        assert isinstance(value, str) and value

def test_removed_id_attributes_are_gone():
    for name in REMOVED:
        assert not hasattr(selectors, name), f"{name} should have been dropped"

def test_url_identity_patterns_present():
    # lessonId from the lesson URL, pupil query param for studentId.
    assert selectors.LESSON_URL_RE.search("/marathon/110326/lesson/1781437").group(1) == "1781437"
    assert selectors.PUPIL_QS == "pupil"
    assert selectors.STUDENT_ID_RE.search("Аян Серик 3176678").group(0) == "3176678"

def test_selector_error_is_exception():
    assert issubclass(SelectorError, Exception)

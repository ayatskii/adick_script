from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.config import Settings
from edvibe_bot.errors import SelectorError


@dataclass
class Student:
    id: str
    name: str
    email: str = ""     # unique → used to target the right student in open_progress


# Virtualised-roster scroll-collect tuning.
_MAX_SCROLLS = 200
_SCROLL_STABLE_PASSES = 6
_SCROLL_WAIT_MS = 800


def _wait_click(page: Page, selector: str, timeout: int = 30000) -> None:
    """Click the first match, waiting for the SPA to render it first.

    `.first` dodges strict-mode duplicates (e.g. two "Фильтр" buttons); the
    explicit visible-wait avoids racing the Vue SPA's async paint after a goto.
    """
    loc = page.locator(selector).first
    loc.wait_for(state="visible", timeout=timeout)
    loc.click()


def apply_curator_filter(page: Page, curator_name: str) -> None:
    """Open Фильтр and narrow the roster to a single curator's students.

    The flow (confirmed live): click "Фильтр" → click the readonly Кураторы input
    to OPEN its dropdown → click the EXACT curator option → assert the input's
    value is now the curator (so we never silently keep the wrong selection) →
    click "Применить". The exact-text match + value assertion guarantee we filter
    to *this* curator and not a same-prefixed one.

    Raises SelectorError if the filter cannot be confirmed applied — far safer
    than the old best-effort path, which silently swallowed failures and graded
    the ENTIRE marathon roster (~198 students) instead of one curator's ~26.
    """
    _wait_click(page, selectors.FILTER_BUTTON, timeout=15000)
    _wait_click(page, selectors.CURATOR_DROPDOWN, timeout=10000)
    # Exact match: "Mister Adilet" must not match another curator. .first guards
    # against an option rendered twice (highlighted + plain).
    page.get_by_text(curator_name, exact=True).first.click(timeout=10000)
    page.wait_for_timeout(500)

    selected = page.locator(selectors.CURATOR_DROPDOWN).first.input_value()
    if (selected or "").strip() != curator_name:
        raise SelectorError(
            f"curator filter not applied: expected {curator_name!r} selected, "
            f"got {selected!r} — refusing to grade the unfiltered roster"
        )
    _wait_click(page, selectors.FILTER_APPLY, timeout=10000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)


def _goto_marathon_direct(page: Page, attempts: int = 4) -> bool:
    """Navigate straight to the roster URL and wait for the SPA to SETTLE on a
    /marathon/ route. Returns True once landed.

    Right after goto, the Vue router can briefly sit on an interstitial/redirect
    URL before resolving to the marathon route — so a single post-goto url check
    races the router and falsely reports a bounce (which then drops us onto the
    flaky Марафоны tab). We re-goto and poll the URL a few times instead."""
    for _ in range(attempts):
        page.goto(selectors.MARATHON_STUDENTS_URL)
        page.wait_for_load_state("networkidle")
        try:
            page.wait_for_url(lambda url: "/marathon/" in url, timeout=8000)
            return True
        except Exception:  # noqa: BLE001 - router still settling; re-goto and retry
            if "/marathon/" in page.url:
                return True
            page.wait_for_timeout(1500)
    return "/marathon/" in page.url


def open_marathon(page: Page, settings: Settings) -> None:
    """Land on the Pre-IELTS marathon roster, then filter to the curator.

    Primary path: navigate DIRECTLY to the roster URL — the classes → Марафоны →
    Pre-IELTS tab flow is a Vue SPA whose "Марафоны" tab intermittently never
    paints (a wait_for timeout that, running outside the per-student boundary,
    kills the whole run). We retry the direct nav (waiting for the /marathon/
    route to settle) and only fall back to the click flow if it truly never lands.

    The curator filter is then REQUIRED (not best-effort): grading the wrong
    teacher's students is a real, irreversible action, so a filter failure raises
    rather than falling back to the full roster.
    """
    if not _goto_marathon_direct(page):
        # Direct URL never settled on /marathon/ (stale session / route change) —
        # last resort: the click flow, itself retried for transient render misses.
        last_exc: "Exception | None" = None
        for _ in range(3):
            try:
                page.goto(selectors.NAV_CLASSES)
                page.wait_for_load_state("networkidle")
                _wait_click(page, selectors.MARATHONS_TAB, timeout=15000)
                _wait_click(page, selectors.PRE_IELTS_CARD, timeout=15000)
                page.wait_for_load_state("networkidle")
                last_exc = None
                break
            except Exception as exc:  # noqa: BLE001 - retry transient SPA render misses
                last_exc = exc
                page.wait_for_timeout(1500)
        if last_exc is not None:
            raise last_exc

    apply_curator_filter(page, settings.curator_name)


def _parse_student_row(text: str) -> "Student | None":
    """PURE: build a Student from one row's text, or None when the row carries no
    numeric id (a stray node in the virtualised list — skip rather than fail)."""
    match = selectors.STUDENT_ID_RE.search(text)
    if not match:
        return None
    student_id = match.group(0)
    email_match = selectors.STUDENT_EMAIL_RE.search(text)
    email = email_match.group(0) if email_match else ""
    return Student(id=student_id, name=_student_name(text, student_id, email), email=email)


def _read_visible_students(page: Page) -> "dict[str, Student]":
    """Parse the currently-rendered student rows into {id: Student}."""
    found: "dict[str, Student]" = {}
    for row in page.locator(selectors.STUDENT_ROW).all():
        student = _parse_student_row(row.inner_text().strip())
        if student is not None:
            found[student.id] = student
    return found


def list_students(page: Page) -> list[Student]:
    """Collect EVERY student in the marathon roster.

    The roster is a virtualised list that lazy-renders rows on scroll, so we
    read → scroll → repeat, accumulating by id, until no new students appear for
    several consecutive passes (or a hard scroll cap). Rows without a numeric id
    are skipped (stray render nodes), not treated as errors."""
    collected: "dict[str, Student]" = {}
    rows = page.locator(selectors.STUDENT_ROW)
    stable = 0
    for _ in range(_MAX_SCROLLS):
        before = len(collected)
        collected.update(_read_visible_students(page))
        stable = 0 if len(collected) > before else stable + 1
        if stable >= _SCROLL_STABLE_PASSES:
            break
        # Advance the virtualised list by pulling the LAST rendered row into view
        # (a window wheel doesn't reach the inner scroll container). This forces
        # the next batch to render; previously-seen ids dedupe.
        try:
            if rows.count() > 0:
                rows.last.scroll_into_view_if_needed(timeout=3000)
        except Exception:  # noqa: BLE001 - keep collecting what we have
            pass
        page.wait_for_timeout(_SCROLL_WAIT_MS)
    return list(collected.values())


def _student_name(text: str, student_id: str, email: str = "") -> str:
    """PURE: the display name is the text BEFORE the id (the row reads
    "<avatar> <name> <id> <email> Прогресс ученика ..."), with the leading
    one-letter avatar initial dropped. Falls back to the email when a student's
    only label IS their email."""
    norm = " ".join(text.split())
    before = norm.split(student_id)[0]
    if email:
        before = before.replace(email, "")
    parts = before.split()
    if parts and len(parts[0]) == 1:   # drop the avatar initial ("A Nurdana" -> "Nurdana")
        parts = parts[1:]
    name = " ".join(parts).strip()
    return name or email or norm.replace(student_id, "").strip()

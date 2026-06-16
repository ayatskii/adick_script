import os

import pytest

from edvibe_bot import selectors
from edvibe_bot.auth import login as auth
from edvibe_bot.config import Settings


def make_settings(tmp_path, **overrides) -> Settings:
    base = dict(
        edvibe_login="teacher@example.com",
        edvibe_password="s3cret",
        openai_api_key="sk-test",
        storage_state_path=str(tmp_path / "storage_state.json"),
    )
    base.update(overrides)
    return Settings(**base)


class FakePage:
    """Mirrors the slice of playwright.sync_api.Page used by auth.login."""

    def __init__(self, land_url: str):
        # url after a goto() resolves to land_url (simulates server redirect)
        self._land_url = land_url
        self.url = ""
        self.goto_calls: list[str] = []
        self.fills: list[tuple[str, str]] = []
        self.clicks: list[str] = []
        self.waited = False

    def goto(self, url, **kwargs):
        self.goto_calls.append(url)
        self.url = self._land_url

    def fill(self, sel, value):
        self.fills.append((sel, value))

    def click(self, sel):
        self.clicks.append(sel)

    def wait_for_load_state(self, state="load", **kwargs):
        self.waited = True


class FakeContext:
    def __init__(self, page: FakePage):
        self._page = page
        self.new_page_calls = 0
        self.storage_state_calls: list[str] = []

    def new_page(self) -> FakePage:
        self.new_page_calls += 1
        return self._page

    def storage_state(self, path=None):
        self.storage_state_calls.append(path)


def test_login_fills_and_clicks_the_right_selectors(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    settings = make_settings(tmp_path)

    auth.login(page, settings)

    assert page.goto_calls == [selectors.LOGIN_URL]
    assert (selectors.LOGIN_EMAIL, settings.edvibe_login) in page.fills
    assert (selectors.LOGIN_PASSWORD, settings.edvibe_password) in page.fills
    assert page.clicks == [selectors.LOGIN_SUBMIT]
    assert page.waited is True


def test_is_session_valid_true_when_landing_authed(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    assert auth.is_session_valid(page) is True
    assert page.goto_calls == [selectors.AUTHED_URL]


def test_is_session_valid_false_when_redirected_to_login(tmp_path):
    page = FakePage(land_url=selectors.LOGIN_URL)
    assert auth.is_session_valid(page) is False


def test_ensure_logged_in_logs_in_and_saves_state_when_no_file(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    ctx = FakeContext(page)
    settings = make_settings(tmp_path)
    assert not os.path.exists(settings.storage_state_path)

    returned = auth.ensure_logged_in(ctx, settings)

    assert returned is page
    assert ctx.new_page_calls == 1
    # fresh login happened
    assert page.goto_calls[0] == selectors.LOGIN_URL
    assert page.clicks == [selectors.LOGIN_SUBMIT]
    # storage_state persisted to the configured path
    assert ctx.storage_state_calls == [settings.storage_state_path]


def test_ensure_logged_in_reuses_valid_state_without_relogin(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    ctx = FakeContext(page)
    settings = make_settings(tmp_path)
    # simulate a pre-existing storage_state file
    with open(settings.storage_state_path, "w") as fh:
        fh.write("{}")

    returned = auth.ensure_logged_in(ctx, settings)

    assert returned is page
    # only the is_session_valid probe ran; no login navigation/submit
    assert page.goto_calls == [selectors.AUTHED_URL]
    assert page.clicks == []
    # no re-save when the session was already valid
    assert ctx.storage_state_calls == []


def test_ensure_logged_in_relogs_in_when_state_is_stale(tmp_path):
    # land on LOGIN_URL first (stale session) then re-login lands AUTHED
    page = FakePage(land_url=selectors.LOGIN_URL)
    ctx = FakeContext(page)
    settings = make_settings(tmp_path)
    with open(settings.storage_state_path, "w") as fh:
        fh.write("{}")

    returned = auth.ensure_logged_in(ctx, settings)

    assert returned is page
    # probe redirected to login => stale => full login() ran (goes to LOGIN_URL)
    assert selectors.LOGIN_URL in page.goto_calls
    assert page.clicks == [selectors.LOGIN_SUBMIT]
    # state re-saved after the fresh login
    assert ctx.storage_state_calls == [settings.storage_state_path]

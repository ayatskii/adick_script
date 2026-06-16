"""Auth: edvibe.com login, session validity, and storage_state reuse.

Browser I/O module. The logic is thin, so no extra pure helpers are extracted;
the I/O sequencing is verified with hand-rolled Playwright doubles. Selectors and
SelectorError already exist (Bootstrap task) and are REFERENCED only.
"""

from __future__ import annotations

import os

from playwright.sync_api import BrowserContext, Page

from edvibe_bot import selectors
from edvibe_bot.config import Settings


def login(page: Page, settings: Settings) -> None:
    """Perform a fresh username/password login on edvibe.com."""
    page.goto(selectors.LOGIN_URL)
    page.fill(selectors.LOGIN_EMAIL, settings.edvibe_login)
    page.fill(selectors.LOGIN_PASSWORD, settings.edvibe_password)
    page.click(selectors.LOGIN_SUBMIT)
    page.wait_for_load_state("networkidle")


def is_session_valid(page: Page) -> bool:
    """Probe an authed URL; the session is valid iff we are NOT bounced to login."""
    page.goto(selectors.AUTHED_URL)
    return page.url != selectors.LOGIN_URL


def ensure_logged_in(context: BrowserContext, settings: Settings) -> Page:
    """Restore a saved storage_state if it is still valid; otherwise log in fresh
    and persist storage_state to settings.storage_state_path. Returns the Page."""
    page = context.new_page()
    if os.path.exists(settings.storage_state_path) and is_session_valid(page):
        return page
    login(page, settings)
    context.storage_state(path=settings.storage_state_path)
    return page

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
    """Perform a fresh username/password login on edvibe.com.

    The login page is a Vue SPA: ``goto`` resolves before the form renders, so we
    wait for networkidle AND the email input to be visible before filling (a bare
    fill races the render and times out), then wait until the URL leaves /login."""
    page.goto(selectors.LOGIN_URL)
    page.wait_for_load_state("networkidle")
    page.locator(selectors.LOGIN_EMAIL).wait_for(state="visible", timeout=30000)
    page.fill(selectors.LOGIN_EMAIL, settings.edvibe_login)
    page.fill(selectors.LOGIN_PASSWORD, settings.edvibe_password)
    page.click(selectors.LOGIN_SUBMIT)
    page.wait_for_url(lambda url: "/login" not in url, timeout=20000)


def is_session_valid(page: Page) -> bool:
    """Probe an authed URL; the session is valid iff we are NOT bounced to login.

    edvibe is a Vue SPA: ``goto`` resolves on the shell load while the URL is
    still the authed route, and only a beat LATER does client-side auth redirect
    an unauthenticated visitor to /login. Checking the URL immediately after goto
    therefore reports a false-positive "valid" — the run then proceeds
    unauthenticated and every subsequent nav bounces to /login. Wait for the SPA
    to settle (networkidle + a short grace) before reading the URL, and match
    /login as a substring (the redirect may carry a ?redirect= query)."""
    page.goto(selectors.AUTHED_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    return "/login" not in page.url


def ensure_logged_in(context: BrowserContext, settings: Settings) -> Page:
    """Restore a saved storage_state if it is still valid; otherwise log in fresh
    and persist storage_state to settings.storage_state_path. Returns the Page."""
    page = context.new_page()
    if os.path.exists(settings.storage_state_path) and is_session_valid(page):
        return page
    login(page, settings)
    context.storage_state(path=settings.storage_state_path)
    return page

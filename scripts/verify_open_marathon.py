"""READ-ONLY: exercise the REAL hardened open_marathon + list_students."""

from __future__ import annotations

from playwright.sync_api import sync_playwright

from edvibe_bot.auth.login import login
from edvibe_bot.config import load_settings
from edvibe_bot.scraper.dashboard import open_marathon, list_students

_STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]
_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def main() -> None:
    settings = load_settings()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=_STEALTH_ARGS)
        page = browser.new_context(user_agent=_UA).new_page()
        try:
            login(page, settings)
            open_marathon(page, settings)        # production path (filter REQUIRED)
            students = list_students(page)
            print(f"curator={settings.curator_name!r} -> {len(students)} students")
            print("sample:", [s.name for s in students[:10]])
            assert 0 < len(students) < 100, "expected a narrowed roster"
            print("OK: real open_marathon filtered to the curator's students.")
        finally:
            browser.close()


if __name__ == "__main__":
    main()

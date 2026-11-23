"""Browser tools — Playwright-driven Chromium, VISIBLE by default.

The browser opens on screen so you (and your friends) can watch the agent
click, type and read, just like a human. Change visible/headless from the
Settings screen (⚙️) in the app — no file editing needed.

The browser uses a PERSISTENT profile (data/browser-profile/, git-ignored):
logins and cookies survive restarts, so once you sign in to Google in the
agent's browser, "Sign in with Google" on other sites just works — no
re-typing passwords every time. First Google sign-in is done once by you,
in the visible browser.

The agent drives sites generically: it opens a page, reads its text and
links, and plans the next click/type from what it sees. There are no
hardcoded selectors for any site — see site-profiles.yaml for optional
per-site notes you can fill in yourself.

Honest limits: CAPTCHAs cannot be solved by the agent (the user solves
them in the visible browser). OTPs CAN be filled by the agent, two ways:
EMAIL OTPs are read from the user's Gmail and filled automatically
(needs the Gmail setup from GMAIL_SETUP.md); SMS OTPs cannot be read
(Satyam has no SMS access), so the agent ASKS the user in chat for the
code ("SMS pe aaya OTP bhejo") and fills it itself when the code comes
— the user never has to type anything into the browser. A user-provided
code is used once for the fill and never stored, logged, or echoed.
"""
import re
from pathlib import Path

from ..config import settings

MAX_TEXT_CHARS = 8000

# Locators (in order) for finding an OTP field on a page.
_OTP_FIELD_SELECTORS = [
    'input[autocomplete="one-time-code"]',
    'input[name*="otp" i], input[id*="otp" i], input[placeholder*="otp" i]',
    'input[name*="verif" i], input[id*="verif" i], '
    'input[placeholder*="verif" i]',
    'input[name*="code" i][inputmode="numeric"], '
    'input[id*="code" i][inputmode="numeric"]',
]


class BrowserSession:
    """One reusable Chromium window, on a persistent profile. Launched
    lazily on first use; logins survive server restarts."""

    def __init__(self):
        self._playwright = None
        self._context = None
        self._page = None

    @property
    def profile_dir(self) -> Path:
        """Chromium profile dir — cookies/logins live here. Under data/
        (git-ignored), so it never lands in a zip or a repo."""
        return settings.data_dir / "browser-profile"

    def _ensure_page(self):
        if self._page is not None:
            return self._page
        from playwright.sync_api import sync_playwright

        try:
            self.profile_dir.mkdir(parents=True, exist_ok=True)
            self._playwright = sync_playwright().start()
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=settings.browser_headless,
                viewport={"width": 1280, "height": 800},
            )
            pages = self._context.pages
            self._page = pages[0] if pages else self._context.new_page()
        except Exception as e:
            raise RuntimeError(
                "Chromium launch nahi ho paya. Kya 'playwright install chromium' "
                f"chala tha? Details: {e}"
            )
        return self._page

    # -- actions ------------------------------------------------------
    def open(self, url: str) -> str:
        page = self._ensure_page()
        if not url.startswith(("http://", "https://", "file://", "data:")):
            url = "https://" + url
        page.goto(url, timeout=30000)
        page.wait_for_timeout(1200)
        return f"Khul gaya: {page.title()} ({page.url})"

    def read(self) -> str:
        page = self._ensure_page()
        text = page.inner_text("body")
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.slice(0, 30).map(a => (a.innerText.trim() || a.href).slice(0, 80) + ' -> ' + a.href)",
        )
        out = f"Page: {page.title()} ({page.url})\n\n{text[:MAX_TEXT_CHARS]}"
        if links:
            out += "\n\nLinks (pehle 30):\n" + "\n".join(links)
        return out

    def click(self, selector: str) -> str:
        page = self._ensure_page()
        # Playwright accepts CSS selectors and "text=..." out of the box.
        page.click(selector, timeout=8000)
        page.wait_for_timeout(1000)
        return f"Click ho gaya: {selector} — ab page: {page.title()} ({page.url})"

    def type(self, selector: str, text: str) -> str:
        page = self._ensure_page()
        try:
            page.fill(selector, text, timeout=8000)
        except Exception:
            # fill kaam na kare (non-input element) toh click + type karo.
            page.click(selector, timeout=8000)
            page.keyboard.type(text)
        return f"Type ho gaya '{text[:60]}' in {selector}"

    def press(self, key: str) -> str:
        page = self._ensure_page()
        page.keyboard.press(key)
        page.wait_for_timeout(800)
        return f"Key dabayi: {key} — ab page: {page.title()} ({page.url})"

    def scroll(self) -> str:
        page = self._ensure_page()
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(600)
        return "Scroll ho gaya (neeche)."

    def screenshot(self, name: str = "shot.png") -> str:
        page = self._ensure_page()
        shots_dir = settings.workspace_dir / "screenshots"
        shots_dir.mkdir(parents=True, exist_ok=True)
        safe = Path(name).name or "shot.png"
        if not safe.endswith(".png"):
            safe += ".png"
        path = shots_dir / safe
        page.screenshot(path=str(path))
        return f"Screenshot save ho gaya: {path}"

    # -- form filling -------------------------------------------------
    def _find_field(self, page, field: dict):
        """Locate one form field by label, name, or placeholder (in that
        order). Returns a Playwright locator, or None when nothing
        visible matches. Never raises."""
        label = (field.get("label") or "").strip()
        name = (field.get("name") or "").strip()
        placeholder = (field.get("placeholder") or "").strip()

        candidates = []
        if label:
            try:
                candidates.append(page.get_by_label(label, exact=False))
            except Exception:
                pass
        if name:
            safe = name.replace("'", "\\'")
            candidates.append(page.locator(
                f"input[name='{safe}'], textarea[name='{safe}'], "
                f"select[name='{safe}']"))
        if placeholder:
            safe = placeholder.replace("'", "\\'")
            candidates.append(page.locator(
                f"input[placeholder*='{safe}'], "
                f"textarea[placeholder*='{safe}']"))
        for loc in candidates:
            try:
                first = loc.first
                if first.count() and first.is_visible():
                    return first
            except Exception:
                continue
        return None

    def fill_form(self, url: str, fields: list, submit: bool = True) -> str:
        """Open a page, fill a form, optionally submit it.

        `fields` is a list of dicts, each with a "value" and at least one
        of "label" / "name" / "placeholder" to find the field, plus an
        optional "type" ("select" / "checkbox" / anything else = text).
        Returns a plain summary of what was filled, what was skipped,
        and where the page ended up. Field VALUES are echoed back only
        truncated (passwords etc. stay out of long logs)."""
        page = self._ensure_page()
        self.open(url)
        filled, skipped = [], []
        last_loc = None
        for field in fields or []:
            if not isinstance(field, dict) or "value" not in field:
                skipped.append("(galat field — value nahi hai)")
                continue
            ident = (field.get("label") or field.get("name")
                     or field.get("placeholder") or "?")
            loc = self._find_field(page, field)
            if loc is None:
                skipped.append(f"{ident} (field nahi mila)")
                continue
            ftype = (field.get("type") or "").strip().lower()
            value = field["value"]
            try:
                if ftype == "select":
                    try:
                        loc.select_option(value=str(value))
                    except Exception:
                        loc.select_option(label=str(value))
                elif ftype == "checkbox":
                    if value in (True, "true", "yes", "1", 1):
                        loc.check()
                    else:
                        loc.uncheck()
                else:
                    loc.fill(str(value))
                filled.append(ident)
                last_loc = loc
            except Exception as e:
                skipped.append(f"{ident} (bhar nahi paya: {e})")
        submitted = ""
        if submit:
            try:
                btn = page.locator(
                    "button[type=submit], input[type=submit]").first
                if btn.count() and btn.is_visible():
                    btn.click(timeout=8000)
                    submitted = " Submit dabaa diya."
                elif last_loc is not None:
                    last_loc.press("Enter")
                    submitted = " Enter dabaa diya (submit button nahi mila)."
                else:
                    submitted = " Submit button nahi mila."
                page.wait_for_timeout(1500)
            except Exception as e:
                submitted = f" Submit karte waqt error aaya: {e}."
        summary = [f"Form khula: {page.title()} ({page.url})."]
        if filled:
            summary.append(f"Bhar diye: {', '.join(filled)}.")
        if skipped:
            summary.append(f"Skip hue: {'; '.join(skipped)}.")
        if submitted:
            summary.append(submitted.strip())
        return " ".join(summary)

    # -- OTP auto-fill ------------------------------------------------
    def _find_otp_field(self, page):
        """Find the OTP input on the current page. Returns (locator, kind)
        where kind is 'single' or 'boxes' (multi-box OTP), or (None, None).
        Never raises."""
        for selector in _OTP_FIELD_SELECTORS:
            try:
                loc = page.locator(selector).first
                if loc.count() and loc.is_visible():
                    return loc, "single"
            except Exception:
                continue
        # Multi-box OTP: several single-char inputs in a row.
        try:
            boxes = page.locator('input[maxlength="1"]')
            if boxes.count() >= 4:
                return boxes, "boxes"
        except Exception:
            pass
        return None, None

    def fill_otp(self, sender: str = "", minutes: int = 10,
                 code: str | None = None) -> str:
        """Fill the OTP on the current page. Two sources:

        * `code` given — a code the USER just typed in chat (an SMS OTP
          the agent asked for). It is used directly, Gmail is never
          consulted, and it is used once for this fill and never stored,
          logged, or echoed back anywhere.
        * `code` omitted — read the code from the user's Gmail (email
          OTPs only; `sender` is the site the OTP came from,
          e.g. 'Internshala'; only emails from the last `minutes`
          minutes count).

        The code itself is NEVER echoed back in the result, whatever
        the source. The page stays open in the persistent browser
        session — the agent must NOT close the browser while waiting
        for the user to send an SMS code, or the OTP page is gone."""
        page = self._ensure_page()
        loc, kind = self._find_otp_field(page)
        if loc is None:
            return ("Is page pe OTP wala field nahi mila — pehle browser_read "
                    "se page dekho, ya jis step pe OTP aata hai wahan tak "
                    "pahuncho, phir dobara bolo.")
        if code is not None:
            code = str(code).strip()
            if not code.isdigit() or not 4 <= len(code) <= 8:
                return ("Wo code sahi nahi lag raha — 4 se 8 digit ka number "
                        "hona chahiye. User se dobara maango (finish answer "
                        "me: 'SMS pe aaya OTP bhejo').")
            source = "user se mila code"
        else:
            from . import gmail_tool

            code = gmail_tool.get_otp_code(sender, minutes=minutes)
            if not code:
                return (
                    f"Pichhle {minutes} minute me '{sender}' se OTP wala "
                    f"email nahi mila — ye SMS OTP lag raha hai, Gmail se "
                    f"nahi milega. User se chat me code maango: finish "
                    f"answer me bas ye likho — 'SMS pe aaya OTP bhejo' — "
                    f"aur browser band mat karo, OTP wala page khula "
                    f"rahega. Jab user code bheje toh browser_fill_otp me "
                    f"code de ke khud bhar do."
                )
            source = f"'{sender}' ke email se liya"
        try:
            if kind == "boxes":
                digits = list(code)[: loc.count()]
                for i, digit in enumerate(digits):
                    loc.nth(i).fill(digit)
            else:
                loc.fill(code)
        except Exception as e:
            return f"OTP field me code bhar nahi paya: {e}"
        return (f"OTP bhar diya ({len(code)}-digit code, {source}). Ab "
                f"Verify/Submit dabao ya bolo toh main dabata hoon.")

    def close(self) -> str:
        # Closing the persistent context also closes its browser; the
        # profile dir (logins/cookies) stays on disk for next time.
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
        self._playwright = None
        self._context = None
        self._page = None
        return "Browser band ho gaya."


# One shared session for the whole agent run.
browser = BrowserSession()


# -- Plain functions the agent calls --------------------------------------
def browser_open(url: str) -> str:
    """Open a URL in the visible Chromium window."""
    return browser.open(url)


def browser_read() -> str:
    """Read the current page's text plus its first 30 links."""
    return browser.read()


def browser_click(selector: str) -> str:
    """Click something: a CSS selector ('button.submit') or text ('text=Login')."""
    return browser.click(selector)


def browser_type(selector: str, text: str) -> str:
    """Type text into a field (CSS selector, e.g. 'input[name=q]')."""
    return browser.type(selector, text)


def browser_press(key: str) -> str:
    """Press a keyboard key, e.g. 'Enter', 'Tab', 'Escape'."""
    return browser.press(key)


def browser_scroll() -> str:
    """Scroll the page down."""
    return browser.scroll()


def browser_screenshot(name: str = "shot.png") -> str:
    """Save a screenshot to workspace/screenshots/."""
    return browser.screenshot(name)


def browser_fill_form(url: str, fields: list, submit: bool = True) -> str:
    """Open a page, fill a form, optionally submit it. fields: a list of
    {"label"|"name"|"placeholder", "value", "type"?} dicts."""
    return browser.fill_form(url, fields, submit=submit)


def browser_fill_otp(sender: str = "", minutes: int = 10,
                     code: str | None = None) -> str:
    """Fill the OTP on the current page. No `code`: read it from Gmail
    (email OTPs only — `sender` = the site, e.g. 'Internshala'). `code`
    given: fill the user-provided code directly (SMS OTP the user just
    typed in chat) — Gmail is never consulted, and the code is used
    once and never stored, logged, or echoed."""
    return browser.fill_otp(sender, minutes=minutes, code=code)


def browser_close() -> str:
    """Close the browser window."""
    return browser.close()

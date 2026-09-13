"""
Shared core logic for the WhatsApp / Email automation agent.
Used by both the CLI (agent.py) and the web UI (server.py) so the
send/contact/LLM logic lives in exactly one place.

WHATSAPP REWRITE -- why pywhatkit had to go, not just get tweaked:
pywhatkit.sendwhatmsg_instantly() calls Python's webbrowser.open() on
every single call. There's no "reuse the tab" mode -- a fresh browser
tab (sometimes a fresh window, depending on OS/browser state) is what
it's designed to do each time. On top of that, it drives the page with
pyautogui -- blind screen-coordinate keypresses with no idea what's
actually on screen. Over a long session, tabs pile up, and if a dialog
or notification popup ever has focus instead of the compose box, a
blind Enter/Ctrl+W lands wherever focus actually is -- which is a very
plausible explanation for crashes that show up "over time" rather than
immediately.

The fix is a persistent Selenium session: ONE Chrome window, opened
once, reused for every send by just navigating it to a new chat --
same tab, no pyautogui, no guessing. Selenium clicks and types into
the actual DOM element it found, not "wherever the mouse happens to
be."
"""
import os
import json
import time
import atexit
import smtplib
import threading
from pathlib import Path
from email.mime.text import MIMEText

from dotenv import load_dotenv
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        f"GROQ_API_KEY not found. Checked: {env_path}\n"
        "Fix checklist:\n"
        "1. Confirm .env sits in the same folder as this script.\n"
        "2. Confirm the file is literally named '.env' -- not '.env.txt'.\n"
        "3. Open .env and confirm the line reads exactly: GROQ_API_KEY=gsk_...\n"
        "4. Restart the terminal/IDE -- some editors cache environment state."
    )

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
# llama-3.3-70b-versatile and llama-3.1-8b-instant were both deprecated by
# Groq (announced June 17, 2026); openai/gpt-oss-20b is Groq's recommended
# replacement and supports the same tool-calling this app relies on.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

CONTACTS_PATH = BASE_DIR / "contacts.json"

# --------------------------------------------------------------------------
# Contacts (local lookup only -- never sent to the LLM)
# --------------------------------------------------------------------------

def load_contacts() -> dict:
    if not CONTACTS_PATH.exists():
        return {}
    with open(CONTACTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(contacts: dict) -> None:
    with open(CONTACTS_PATH, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)


def resolve_contact(name: str, platform: str) -> str | None:
    """Look up a saved contact by name and return their phone/email for the
    given platform ('whatsapp' or 'email'). Case-insensitive. Returns None
    if there's no contact, or the relevant field is empty."""
    contacts = load_contacts()
    entry = contacts.get(name.strip().lower())
    if not entry:
        return None
    field = "phone" if platform == "whatsapp" else "email"
    value = (entry.get(field) or "").strip()
    return value or None


def upsert_contact(name: str, phone: str = "", email: str = "") -> None:
    contacts = load_contacts()
    key = name.strip().lower()
    entry = contacts.get(key, {})
    if phone:
        entry["phone"] = phone.strip()
    if email:
        entry["email"] = email.strip()
    entry.setdefault("display_name", name.strip())
    contacts[key] = entry
    save_contacts(contacts)


def delete_contact(name: str) -> None:
    contacts = load_contacts()
    contacts.pop(name.strip().lower(), None)
    save_contacts(contacts)


# --------------------------------------------------------------------------
# WhatsApp -- one persistent Selenium session, reused for every send
# --------------------------------------------------------------------------
_driver = None
_automation_lock = threading.Lock()  # serialize sends; one browser, one user


def _get_driver():
    """Return the live browser session, starting one if needed. The
    profile directory persists your WhatsApp Web login across server
    restarts, so you shouldn't have to rescan the QR code every time
    you start the server -- only the very first run, and again if the
    session eventually expires."""
    global _driver
    if _driver is not None:
        try:
            _ = _driver.title  # cheap check that the window/session is alive
            return _driver
        except Exception:
            _driver = None  # session died -- fall through and recreate

    profile_dir = os.getenv("WA_CHROME_PROFILE", str(BASE_DIR / ".whatsapp_chrome_profile"))
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--start-maximized")
    # Deliberately NOT headless -- this automation is meant to be visible.
    _driver = webdriver.Chrome(options=options)
    _driver.get("https://web.whatsapp.com")
    return _driver


def _ensure_logged_in(driver, first_run_timeout: int = 120):
    """Wait for the chat list to appear. Quick check first (already logged
    in from a previous run); if that fails, wait longer for a first-time
    QR scan."""
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chat list']"))
        )
        return
    except TimeoutException:
        pass
    WebDriverWait(driver, first_run_timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chat list']"))
    )


def ensure_whatsapp_ready(timeout: int = 120) -> None:
    """Call this once when the server starts, not on first send. Opens the
    browser and blocks until you're logged in (or the profile already has
    a saved session, in which case it returns almost immediately) -- so a
    first-time QR scan happens during your own setup, never live in front
    of an audience."""
    driver = _get_driver()
    _ensure_logged_in(driver, first_run_timeout=timeout)


@atexit.register
def _shutdown_driver():
    global _driver
    if _driver is not None:
        try:
            _driver.quit()
        except Exception:
            pass
        _driver = None


def is_success(result: str) -> bool:
    return not result.startswith("Failed")


def send_whatsapp(phone_number: str, message: str) -> str:
    with _automation_lock:  # one automation call at a time, always
        try:
            driver = _get_driver()
            _ensure_logged_in(driver)

            phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
            driver.get(f"https://web.whatsapp.com/send?phone={phone}")

            # For numbers not already in your chat list, WhatsApp Web shows
            # an intermediate "Continue to Chat" button -- click through it
            # if present, otherwise the chat opened directly.
            try:
                continue_btn = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[text()='Continue to Chat']"))
                )
                continue_btn.click()
            except TimeoutException:
                pass

            box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
            )
            box.click()
            for i, line in enumerate(message.split("\n")):
                if i > 0:
                    box.send_keys(Keys.SHIFT, Keys.ENTER)
                box.send_keys(line)
            box.send_keys(Keys.ENTER)

            return f"WhatsApp message sent to {phone_number}"
        except TimeoutException:
            return (
                "Failed to send WhatsApp message: WhatsApp Web didn't respond in time "
                "(check the browser window, your connection, or whether you're still logged in)."
            )
        except Exception as e:
            return f"Failed to send WhatsApp message: {e}"


# --------------------------------------------------------------------------
# Email -- unchanged, smtplib is already reliable here
# --------------------------------------------------------------------------

def send_email(to_email: str, subject: str, body: str) -> str:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not smtp_user or not smtp_pass:
        return "Failed: email credentials not configured. Set SMTP_USER and SMTP_PASS in .env"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        return f"Email sent to {to_email}"
    except Exception as e:
        return f"Failed to send email: {e}"


# --------------------------------------------------------------------------
# LLM tool definitions
# --------------------------------------------------------------------------

# Used by the CLI (agent.py): model picks which platform AND supplies the
# raw contact detail itself, since the CLI has no local contact book.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp",
            "description": "Send a WhatsApp text message to a contact using their phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Recipient's phone number in international format, e.g. +919876543210",
                    },
                    "message": {"type": "string", "description": "The message text to send"},
                },
                "required": ["phone_number", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to a recipient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body text"},
                },
                "required": ["to_email", "subject", "body"],
            },
        },
    },
]

# Used by the web UI: platform AND contact are already chosen by the user
# via dropdowns, so the model's only job is turning the casual instruction
# into an actual message worth sending.
INTENT_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "compose_message",
            "description": (
                "Turn the user's casual instruction into the real message text "
                "to send -- not a restatement of the instruction. "
                "E.g. 'tell her I'm running late' becomes something like "
                "'Hey, running about 10 minutes late, sorry!'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "A short email subject line. Only relevant for email; use '' for WhatsApp.",
                    },
                    "message": {
                        "type": "string",
                        "description": "The full message/body text to send, written naturally based on the request.",
                    },
                },
                "required": ["message"],
            },
        },
    }
]


def extract_intent(user_command: str, platform: str, contact_display_name: str = "") -> dict:
    """Turn free text into {subject, message} for the given platform and recipient."""
    who = f" to {contact_display_name}" if contact_display_name else ""
    system = (
        f"You turn a user's casual instruction into an actual message{who}, "
        f"ready to send over {platform}. Write the real message text, keeping it "
        "natural and appropriately brief. Always call compose_message."
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_command},
        ],
        tools=INTENT_TOOL,
        tool_choice={"type": "function", "function": {"name": "compose_message"}},
        temperature=0.3,
        max_tokens=512,
    )
    call = response.choices[0].message.tool_calls[0]
    return json.loads(call.function.arguments)
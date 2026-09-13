"""
Standalone Chrome/Selenium launch diagnostic -- NOT part of the app itself.
Run directly: python diagnose_chrome.py

This isolates the Chrome launch from the rest of the app (no Flask, no
threading, no WhatsApp profile) and writes chromedriver's own log to
chromedriver_diag.log in this folder. That log usually states the actual
reason Chrome's process exited (missing dependency, blocked by policy,
permission denied, etc.) -- detail the wrapped "crashed" exception hides.

Uses a throwaway temp profile, so it can't be affected by anything in
.whatsapp_chrome_profile, and won't touch your real WhatsApp login.
"""
import sys
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

profile_dir = tempfile.mkdtemp(prefix="chrome_diag_")
print(f"Using throwaway profile: {profile_dir}")

options = webdriver.ChromeOptions()
options.add_argument(f"--user-data-dir={profile_dir}")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(log_output="chromedriver_diag.log")

print("Launching Chrome...")
try:
    driver = webdriver.Chrome(options=options, service=service)
except Exception as e:
    print(f"\nLaunch failed: {e}")
    print("\nCheck chromedriver_diag.log in this folder for the detailed reason.")
    sys.exit(1)

print("Chrome launched successfully.")
driver.get("https://example.com")
print("Page title:", driver.title)
driver.quit()
print("\nSuccess -- Chrome/Selenium works in isolation. If the main app still")
print("fails, the problem is specific to the .whatsapp_chrome_profile folder")
print("or something in agent_core.py's launch options, not Chrome/Selenium itself.")
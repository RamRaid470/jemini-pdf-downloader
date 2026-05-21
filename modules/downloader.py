import os
import logging
from playwright.sync_api import sync_playwright

DOWNLOAD_DIR = os.path.abspath("downloads")

def attempt_login(page, username, password):
    logging.info("🌐 Navigating to login page...")
    page.goto("https://acrow.jemini.com/signin.zul")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    logging.info("🔑 Entering credentials...")
    user_locator = page.locator("[data-sel-id='signin-username-input']")
    user_locator.wait_for(state="attached", timeout=30000)
    user_locator.evaluate("(el, value) => { el.value = value; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); el.dispatchEvent(new Event('blur', { bubbles: true })); }", username)

    pass_locator = page.locator("input[type='password']")
    pass_locator.wait_for(state="attached", timeout=30000)
    pass_locator.evaluate("(el, value) => { el.value = value; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); el.dispatchEvent(new Event('blur', { bubbles: true })); }", password)

    page.get_by_role("button", name="Sign in").click()

    try:
        page.get_by_text("Payslips", exact=True).wait_for(state="visible", timeout=10000)
        logging.info("✅ Sign-in verified successfully!")
        return True
    except Exception:
        logging.warning("⚠️ Sign-in verification failed.")
        return False

def get_payslip(username, password, only_new=False):
    """Runs Playwright. Returns file path if successful, or None if only_new is True and file already exists."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        max_retries = 3
        login_successful = False

        for attempt in range(1, max_retries + 1):
            logging.info(f"🔄 Login Attempt {attempt} of {max_retries}...")
            login_successful = attempt_login(page, username, password)
            if login_successful:
                break
            if attempt < max_retries:
                page.wait_for_timeout(5000)

        if not login_successful:
            browser.close()
            raise Exception("Failed to log in after max retries.")

        logging.info("📂 Navigating to Payslips section...")
        page.wait_for_timeout(4000)
        page.get_by_text("Payslips", exact=True).click(force=True)
        
        logging.info("⏳ Preparing download...")
        page.wait_for_timeout(3000)
        download_button = page.get_by_role("button", name="Download")
        download_button.wait_for(state="visible", timeout=60000)

        with page.expect_download() as download_info:
            download_button.click()

        download = download_info.value
        filename = download.suggested_filename
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        # 🚀 NEW LOGIC: Check if we already have this exact file
        if only_new and os.path.exists(file_path):
            logging.info(f"⏩ Portal is still showing '{filename}'. We already have this.")
            browser.close()
            return None # Return None to tell the master script no new file was found
        
        download.save_as(file_path)
        logging.info(f"✔ Download complete! Saved at: {file_path}")
        browser.close()
        return file_path

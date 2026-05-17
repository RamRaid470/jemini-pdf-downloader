import base64
import os
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

# Load environment variables from .env file
load_dotenv()

# Portal Credentials
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Secure API Configurations
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# Document Encryption Key
PDF_PASSWORD = os.getenv("PDF_PASSWORD")

DOWNLOAD_DIR = os.path.abspath("downloads")


def attempt_login(page):
    print("🌐 Navigating to login page...")
    page.goto("https://acrow.jemini.com/signin.zul")

    print("⏳ Waiting for website components to stabilize...")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    print("🔑 Entering credentials...")

    # 1. Target and fully simulate interaction for Username
    username = page.locator("[data-sel-id='signin-username-input']")
    username.wait_for(state="attached", timeout=30000)

    username.evaluate(
        """(el, value) => {
        el.value = value;
        el.dispatchEvent(new Event('focus', { bubbles: true }));
        el.dispatchEvent(new Event('mousedown', { bubbles: true }));
        el.click();
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
    }""",
        USERNAME,
    )

    # 2. Target and fully simulate interaction for Password
    password = page.locator("input[type='password']")
    password.wait_for(state="attached", timeout=30000)

    password.evaluate(
        """(el, value) => {
        el.value = value;
        el.dispatchEvent(new Event('focus', { bubbles: true }));
        el.dispatchEvent(new Event('mousedown', { bubbles: true }));
        el.click();
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
    }""",
        PASSWORD,
    )

    page.wait_for_timeout(500)

    print("🚀 Clicking sign in...")
    page.get_by_role("button", name="Sign in").click()

    # Verify if login succeeded by checking for the Payslips element
    print("👀 Verifying dashboard access...")
    try:
        payslips = page.get_by_text("Payslips", exact=True)
        payslips.wait_for(state="visible", timeout=10000)
        print("✅ Sign-in verified successfully!")
        return True
    except Exception:
        print("⚠️ Sign-in verification failed (Dashboard element not found).")
        return False


def encrypt_pdf(file_path, password):
    """Reads the downloaded PDF, encrypts it, and overwrites the original file securely."""
    if not password:
        print("⚠️ No PDF_PASSWORD found in environment setup. Skipping encryption.")
        return

    print("🔒 Encrypting PDF document locally...")
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()

        # Copy all pages from the original PDF to the new encrypted writer object
        for page in reader.pages:
            writer.add_page(page)

        # Encrypt the document using the password from your .env file
        writer.encrypt(password)

        # Overwrite the original file with the new encrypted version
        with open(file_path, "wb") as f:
            writer.write(f)
        print("🔒 PDF successfully encrypted and locked down!")
    except Exception as e:
        print(f"❌ Failed to encrypt PDF. Error: {e}")


def send_email_via_api(file_path):
    print("📨 Preparing secure API email payload...")
    filename = os.path.basename(file_path)

    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
            encoded_content = base64.b64encode(file_content).decode("utf-8")

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "from": "onboarding@resend.dev",
            "to": RECEIVER_EMAIL,
            "subject": f"Automated Secured Document: {filename}",
            "html": (
                "<p>Hello,</p><p>Please find attached your automatically downloaded"
                f" document: <strong>{filename}</strong>.</p><p><strong>Note:</strong>"
                " This PDF file has been encrypted locally for your privacy. Please use"
                " your pre-configured master password to open it.</p>"
            ),
            "attachments": [{"content": encoded_content, "filename": filename}],
        }

        print("📤 Broadcasting secure HTTPS request to Resend API...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)

        if response.status_code in [200, 201]:
            print("📧 Email delivered successfully through the API!")
        else:
            print(
                f"❌ API rejected the email. Code: {response.status_code},"
                f" Response: {response.text}"
            )

    except Exception as e:
        print(f"❌ Failed to handle API transmission. Error: {e}")


def run():
    with sync_playwright() as p:
        print("🤖 Launching background automated browser (headless mode)...")
        browser = p.chromium.launch(headless=True)

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Retry Configuration Loop
        max_retries = 3
        login_successful = False

        for attempt in range(1, max_retries + 1):
            print(f"\n🔄 Login Attempt {attempt} of {max_retries}...")
            login_successful = attempt_login(page)

            if login_successful:
                break

            if attempt < max_retries:
                print("⏳ Waiting 5 seconds before trying again...")
                page.wait_for_timeout(5000)

        if not login_successful:
            print(f"❌ Failed to log in after {max_retries} attempts. Exiting.")
            browser.close()
            return

        # Stabilize
        print("⏸ Pausing for 4 seconds to let the main dashboard stabilize...")
        page.wait_for_timeout(4000)

        print("📂 Navigating to Payslips section...")
        payslips = page.get_by_text("Payslips", exact=True)
        payslips.click(force=True)

        print("⏸ Pausing for 3 seconds to let the Payslips view settle...")
        page.wait_for_timeout(3000)

        print("⏳ Preparing download...")
        download_button = page.get_by_role("button", name="Download")
        download_button.wait_for(state="visible", timeout=60000)

        print("⬇ Clicking download button...")
        with page.expect_download() as download_info:
            download_button.click()

        download = download_info.value

        file_path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
        download.save_as(file_path)

        print("✔ Download complete!")
        print(f"📄 File saved locally at: {file_path}")

        # 🚀 NEW LAYER: Intercept the downloaded file and encrypt it before sending
        encrypt_pdf(file_path, PDF_PASSWORD)

        # Dispatch the document via Email API
        send_email_via_api(file_path)

        print("🏁 Automation complete. Shutting down browser context.")
        browser.close()


if __name__ == "__main__":
    run()

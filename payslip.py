import argparse
import logging
import os
import time
from dotenv import load_dotenv

from modules.downloader import get_payslip
from modules.encryptor import encrypt_pdf
from modules.emailer import send_email_via_api

# Setup Logging
LOG_FILE = os.path.abspath("automation.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# Load Environment Variables
load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
PDF_PASSWORD = os.getenv("PDF_PASSWORD")

def main():
    parser = argparse.ArgumentParser(description="Jemini Payslip Automation Pipeline")
    parser.add_argument("--encrypt", action="store_true", help="Apply local AES-256 encryption")
    parser.add_argument("--email", action="store_true", help="Send the downloaded file via the Resend API")
    parser.add_argument("--new", action="store_true", help="Smart polling: check every 15 mins until a new payslip is released")
    args = parser.parse_args()

    logging.info("🎬 Starting automated execution cycle...")

    try:
        file_path = None

        if args.new:
            logging.info("🕵️ Smart Polling Enabled: Looking for unpublished payslip.")
            max_attempts = 16 # Limits polling to 4 hours total (16 attempts * 15 mins)
            
            for attempt in range(1, max_attempts + 1):
                file_path = get_payslip(USERNAME, PASSWORD, only_new=True)
                
                if file_path:
                    logging.info("🎉 Brand new payslip acquired!")
                    break # Break out of the waiting loop, we got it!
                else:
                    if attempt < max_attempts:
                        logging.info(f"⏳ Attempt {attempt}/{max_attempts}: No new payslip yet. Sleeping for 15 minutes...")
                        time.sleep(900) # Sleep for 900 seconds (15 minutes)
            
            # If we went through all 16 attempts and still have no file
            if not file_path:
                logging.warning("🛑 4 hours passed with no new payslip uploaded. Exiting to prevent infinite loop.")
                return 

        else:
            # Normal behavior: just download whatever is there and overwrite/save it
            file_path = get_payslip(USERNAME, PASSWORD, only_new=False)

        # Step 2: Encrypt if the flag was passed
        if args.encrypt and file_path:
            encrypt_pdf(file_path, PDF_PASSWORD)

        # Step 3: Email if the flag was passed
        if args.email and file_path:
            send_email_via_api(file_path, RESEND_API_KEY, RECEIVER_EMAIL, is_encrypted=args.encrypt)

        logging.info("🏁 Pipeline completed successfully.")

    except Exception as e:
        logging.critical(f"💥 Critical Script Failure: {e}")

if __name__ == "__main__":
    main()

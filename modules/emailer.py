import os
import base64
import requests
import logging

def send_email_via_api(file_path, api_key, receiver_email, is_encrypted=False):
    """Sends the document via Resend API."""
    logging.info("📨 Preparing secure API email payload...")
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        encoded_content = base64.b64encode(f.read()).decode("utf-8")

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    encryption_note = "<p><strong>Note:</strong> This file is password-protected.</p>" if is_encrypted else ""

    payload = {
        "from": "onboarding@resend.dev",
        "to": receiver_email,
        "subject": f"Automated Secured Document: {filename}",
        "html": f"<p>Hello,</p><p>Please find attached your document: <strong>{filename}</strong>.</p>{encryption_note}",
        "attachments": [{"content": encoded_content, "filename": filename}],
    }

    try:
        logging.info("📤 Broadcasting secure HTTPS request to Resend API...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code in [200, 201]:
            logging.info("📧 Email delivered successfully through the API!")
        else:
            logging.error(f"❌ API rejected email delivery. Code: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Network communication failure: {e}")

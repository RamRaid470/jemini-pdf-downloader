# Jemini Portal Document Extractor & Secure Transit Pipeline

A specialized, single-user modular automation CLI designed to authenticate into a Jemini HR portal, extract payroll documentation via headless browser automation, and securely forward the asset using localized cryptography and an API abstraction layer. 

This repository serves as a personal implementation log and configuration blueprint.

---

## 🔒 Security Architecture & Threat Modeling

Because this script processes highly sensitive financial and personally identifiable information (PII), the architecture is designed around a strict zero-trust pipeline regarding transit providers and cloud logs.

### Cryptographic Isolation (Payload vs. Metadata)
*   **The Mitigation:** The script intercepts the raw PDF locally using `pypdf` *before* any networking logic is invoked. It applies **AES-256 encryption** using a **mandatory 128-character randomly generated key**.
*   **Cryptographic Boundary:** A 128-character high-entropy string completely saturates the keyspace capabilities of AES-256. This renders the payload mathematically unfeasible to brute-force by any modern compute array. **Using anything less than a 128-character high-entropy key violates the core security assumptions of this blueprint.**

### API Vector vs. Traditional SMTP
Traditional automation scripts rely on raw SMTP configurations. This script drops SMTP entirely in favor of an **outbound HTTPS API token** (Resend). If the API key is intercepted, it only grants scoped execution rights to *send* payloads via a sandbox/domain router. It cannot be used to log into an inbox or read historical data.

---

## 📂 Structural Overview

The application utilizes a modular, Separation of Concerns architecture:

```text
├── modules/
│   ├── __init__.py        # Module namespace initializer
│   ├── downloader.py      # Playwright interactions & Smart Polling
│   ├── encryptor.py       # AES-256 pypdf cryptography
│   └── emailer.py         # Resend HTTPS API router
├── payslip.py             # Master CLI Controller
├── .example.env           # Template for runtime environment variables
└── requirements.txt       # Static Python package state
```

---

## ⚙️ Local Runtime Setup

### 1. Virtual Environment Target Initialization
Isolate the runtime space from the host OS packages:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Runtime Environment Vector (`.env`)
Create a local `.env` block in the project root. Ensure the `PDF_PASSWORD` meets the exact character length specification.
```env
USERNAME="your_portal_username"
PASSWORD="your_portal_password"
RESEND_API_KEY="re_your_secret_token"
RECEIVER_EMAIL="your_inbox@example.com"
# CRITICAL: Must be a randomly generated 128-character string
PDF_PASSWORD="your_128_character_random_high_entropy_string"
```

---

## 💻 CLI Usage & Execution Flags

The master script (`payslip.py`) uses a modular Command Line Interface (CLI). 

**Base Behavior:** If you run `python payslip.py` with no flags, the script simply logs in, downloads the most recent payslip to the local `downloads/` directory as an unencrypted PDF, and shuts down.

To trigger the advanced modules, append the following `--` flags to your command. You can stack them in any order.

### `--new` (Smart Polling)
*   **What it does:** Prevents the script from downloading duplicate/old files.
*   **How it works:** It logs into the portal and checks the filename of the currently available payslip. If that exact filename already exists in your local `downloads/` folder, it assumes HR hasn't published the new one yet.
*   **The Loop:** It closes the browser, sleeps for exactly 15 minutes, and checks again. It will repeat this up to 16 times (4 hours) before cleanly exiting to prevent infinite looping. 

### `--encrypt` (Local AES-256 Lock)
*   **What it does:** Secures the downloaded document before it can be transmitted.
*   **How it works:** Immediately after the PDF hits your local disk, the script intercepts it, applies the 128-character `PDF_PASSWORD` from your `.env` file using AES-256 encryption, and overwrites the original unencrypted file. 

### `--email` (API Transmission)
*   **What it does:** Dispatches the final file to your specified inbox.
*   **How it works:** Converts the local PDF into a Base64 payload and transmits it via outbound HTTPS to the Resend API. If `--encrypt` was also used, it will safely transmit the cryptographically locked version.

---

## 🚀 Execution Examples

**1. Manual Local Extraction**
Downloads the current payslip (unencrypted, no email).
```bash
python payslip.py
```

**2. The Secure Export**
Downloads the file, encrypts it with your 128-char key, and emails it. (Great for manual runs).
```bash
python payslip.py --encrypt --email
```

**3. The Fully Automated Cron Job Pipeline**
Waits for the *newest* file to be uploaded by HR, then securely encrypts and emails it.
```bash
python payslip.py --new --encrypt --email
```

*(Example Cron implementation on Proxmox LXC: `sh -c "/usr/sbin/pct exec 112 -- bash -c 'cd /root/jemini-pdf-downloader && ./venv/bin/python3 payslip.py --new --encrypt --email'" `)*

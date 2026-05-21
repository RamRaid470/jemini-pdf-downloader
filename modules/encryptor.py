import logging
from pypdf import PdfReader, PdfWriter

def encrypt_pdf(file_path, password):
    """Encrypts a PDF in place using AES-256."""
    if not password:
        raise ValueError("Encryption requested but no PDF_PASSWORD found.")

    logging.info("🔒 Encrypting PDF document locally...")
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        with open(file_path, "wb") as f:
            writer.write(f)
            
        logging.info("🔒 PDF successfully encrypted and locked down!")
    except Exception as e:
        logging.error(f"❌ Failed to encrypt PDF. Error: {e}")
        raise e

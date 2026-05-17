# Jemini Portal Document Extractor & Secure Transit Pipeline

A specialized single-user automation utility designed to authenticate into a Jemini HR portal, extract payroll documentation via headless browser automation, and securely forward the asset using localized cryptography and an API abstraction layer. 

This repository serves as a personal implementation log and configuration blueprint.

---

## 🔒 Security Architecture & Threat Modeling

Because this script processes highly sensitive financial and personally identifiable information (PII), the architecture is designed around a strict zero-trust pipeline regarding transit providers and cloud logs.

```text
[Jemini Portal] 
       │
       │ (HTTPS / TLS 1.3)
       ▼
[Local Machine (Arch Linux)] ──► [Applies AES-256 Encryption (MUST use 128-char Key)]
       │
       │ (HTTPS Payload / Opaque Base64 Blob)
       ▼
[Resend API Cloud Router]
       │
       │ (Opportunistic TLS)
       ▼
[Destination Inbox]

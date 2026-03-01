## PDF Email Sender

This project generates a PDF file and emails it to your destination address.

### Setup

1. Use Python 3.9+.
2. Configure environment variables:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="you@example.com"
export SMTP_PASS="your-app-password"
export SMTP_FROM="you@example.com"      # optional, defaults to SMTP_USER
export SMTP_TO="you@example.com"
export SMTP_USE_SSL="false"              # true for port 465
export SMTP_USE_STARTTLS="true"          # usually true for port 587
```

### Run

```bash
python3 pdf_emailer.py
```

It will create `output/report_YYYYMMDD_HHMMSS.pdf` and send it as an email attachment.

### Quick troubleshooting

- **Authentication failed**: use an app-specific password (Gmail/Outlook often require this).
- **Timeout/network error**: verify SMTP host/port and firewall settings.
- **Email sent but no attachment**: check that the generated file exists under `output/`.
- **Spam filtering**: check junk/spam folder, especially on first send.

### Test

```bash
python3 -m unittest -v
```

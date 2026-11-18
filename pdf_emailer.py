"""Generate a PDF and email it as an attachment.

Usage:
    python pdf_emailer.py

Environment variables:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    SMTP_FROM, SMTP_TO,
    SMTP_USE_SSL (true/false), SMTP_USE_STARTTLS (true/false)
"""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


class ConfigError(ValueError):
    """Raised when required configuration is missing."""


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def generate_simple_pdf(output_path: Path, title: str, body: str) -> Path:
    """Generate a minimal valid one-page PDF without extra dependencies."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Escape characters used in PDF text syntax.
    safe_title = title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    safe_body = body.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    stream = (
        "BT\n"
        "/F1 22 Tf\n"
        "72 760 Td\n"
        f"({safe_title}) Tj\n"
        "/F1 12 Tf\n"
        "0 -40 Td\n"
        f"({safe_body}) Tj\n"
        "ET\n"
    )
    stream_bytes = stream.encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii") + stream_bytes + b"endstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )

    output_path.write_bytes(pdf)
    return output_path


def build_email_with_attachment(
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    attachment_path: Path,
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    pdf_bytes = attachment_path.read_bytes()
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=attachment_path.name,
    )
    return msg


def send_via_smtp(
    host: str,
    port: int,
    user: str,
    password: str,
    message: EmailMessage,
    use_ssl: bool,
    use_starttls: bool,
) -> None:
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=30) as server:
            server.login(user, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        if use_starttls:
            server.starttls()
            server.ehlo()
        server.login(user, password)
        server.send_message(message)


def load_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    try:
        smtp_host = load_required_env("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = load_required_env("SMTP_USER")
        smtp_pass = load_required_env("SMTP_PASS")
        sender = os.getenv("SMTP_FROM", smtp_user)
        recipient = load_required_env("SMTP_TO")

        use_ssl = _as_bool(os.getenv("SMTP_USE_SSL"), default=False)
        use_starttls = _as_bool(os.getenv("SMTP_USE_STARTTLS"), default=not use_ssl)

        out_dir = Path("output")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_file = out_dir / f"report_{timestamp}.pdf"

        generate_simple_pdf(
            pdf_file,
            title="Generated PDF Report",
            body=f"Created at {datetime.now().isoformat(timespec='seconds')}",
        )

        message = build_email_with_attachment(
            sender=sender,
            recipient=recipient,
            subject="Your generated PDF",
            body="Attached is your generated PDF report.",
            attachment_path=pdf_file,
        )

        send_via_smtp(
            host=smtp_host,
            port=smtp_port,
            user=smtp_user,
            password=smtp_pass,
            message=message,
            use_ssl=use_ssl,
            use_starttls=use_starttls,
        )

        print(f"Success: sent {pdf_file} to {recipient}")
        return 0
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - runtime failure output
        print(f"Failed to send email: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import patch

import pdf_emailer


class PdfEmailerTests(unittest.TestCase):
    def test_generate_pdf_creates_valid_header(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.pdf"
            pdf_emailer.generate_simple_pdf(path, "Title", "Body")
            data = path.read_bytes()
            self.assertTrue(data.startswith(b"%PDF-1.4"))
            self.assertIn(b"%%EOF", data)

    def test_build_email_has_pdf_attachment(self):
        with tempfile.TemporaryDirectory() as td:
            pdf_path = Path(td) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n...\n%%EOF")
            msg = pdf_emailer.build_email_with_attachment(
                sender="sender@example.com",
                recipient="to@example.com",
                subject="Subject",
                body="Body",
                attachment_path=pdf_path,
            )

            self.assertIsInstance(msg, EmailMessage)
            attachments = list(msg.iter_attachments())
            self.assertEqual(1, len(attachments))
            self.assertEqual("application/pdf", attachments[0].get_content_type())

    @patch("pdf_emailer.smtplib.SMTP")
    def test_send_uses_starttls_when_requested(self, smtp_cls):
        server = smtp_cls.return_value.__enter__.return_value
        msg = EmailMessage()
        pdf_emailer.send_via_smtp(
            host="smtp.example.com",
            port=587,
            user="user",
            password="pass",
            message=msg,
            use_ssl=False,
            use_starttls=True,
        )
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("user", "pass")
        server.send_message.assert_called_once_with(msg)


if __name__ == "__main__":
    unittest.main()

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class MailtrapAPIBackend(BaseEmailBackend):
    """
    Sends email via Mailtrap's HTTP API (port 443) instead of SMTP.
    Avoids outbound SMTP port blocks on Railway.
    """
    API_URL = "https://send.api.mailtrap.io/api/send"

    def send_messages(self, email_messages):
        api_token = getattr(settings, "MAILTRAP_API_TOKEN", "")
        if not api_token:
            if not self.fail_silently:
                raise RuntimeError("MAILTRAP_API_TOKEN is not set.")
            return 0

        sent = 0
        for message in email_messages:
            payload = {
                "from": {"email": message.from_email},
                "to": [{"email": r} for r in message.to],
                "subject": message.subject,
                "text": message.body,
            }

            for content, mimetype in getattr(message, "alternatives", []):
                if mimetype == "text/html":
                    payload["html"] = content

            try:
                resp = requests.post(
                    self.API_URL,
                    json=payload,
                    headers={"Authorization": f"Bearer {api_token}"},
                    timeout=10,
                )
                resp.raise_for_status()
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

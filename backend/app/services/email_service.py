import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Envoie un email de notification. Échec silencieux toléré (log seulement) :
    une notification ratée ne doit jamais faire échouer l'action qui la déclenche."""
    if not settings.smtp_host:
        logger.info("SMTP non configuré, notification ignorée (to=%s, subject=%s)", to, subject)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from or settings.smtp_user or settings.admin_email
    message["To"] = to
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        logger.exception("Échec d'envoi d'email à %s", to)

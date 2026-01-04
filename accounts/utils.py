from __future__ import annotations

from django.core.mail import mail_admins


def send_admin_alert(subject: str, message: str, *, error_text: str | None = None) -> None:
    html_parts = [f"<h1 style=\"color:red\">{subject}</h1>", f"<p>{message}</p>"]
    if error_text:
        html_parts.append(
            f"<div style=\"background:red;color:white;padding:8px\">{error_text}</div>"
        )
    html_message = "\n".join(html_parts)
    mail_admins(subject, message, html_message=html_message)

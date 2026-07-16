from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any


def send_email(config: dict[str, Any], subject: str, markdown_body: str, html_body: str) -> None:
    mail_config = config["mail"]
    host = _required_env(mail_config["smtp_host_env"])
    port = int(os.getenv(mail_config["smtp_port_env"], "465"))
    user = _required_env(mail_config["smtp_user_env"])
    password = _required_env(mail_config["smtp_password_env"])
    sender = os.getenv(mail_config["smtp_from_env"], user)
    recipients = _split_recipients(_required_env(mail_config["smtp_to_env"]))
    use_ssl = _env_bool(mail_config["smtp_use_ssl_env"], default=True)
    use_starttls = _env_bool(mail_config["smtp_use_starttls_env"], default=False)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(markdown_body)
    message.add_alternative(html_body, subtype="html")

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if use_starttls:
                smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(message)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少环境变量: {name}")
    return value


def _split_recipients(value: str) -> list[str]:
    return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

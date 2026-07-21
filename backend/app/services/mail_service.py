"""Transactional email via Gmail SMTP (preferred) or Brevo REST/SMTP fallback."""

from __future__ import annotations

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MailService:
    """Send transactional mail. Display name defaults to ExtractAI."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        if self._gmail_ready():
            return True
        return bool(self._settings.brevo_api_key and self._sender_email())

    def _gmail_ready(self) -> bool:
        user = (self._settings.smtp_user or self._settings.brevo_sender_email or "").strip()
        password = (self._settings.smtp_password or "").replace(" ", "").strip()
        return bool(user and password)

    def _sender_email(self) -> str:
        return (
            (self._settings.mail_from_email or "").strip()
            or (self._settings.smtp_user or "").strip()
            or (self._settings.brevo_sender_email or "").strip()
        )

    def _sender_name(self) -> str:
        return (
            (self._settings.mail_from_name or "").strip()
            or (self._settings.brevo_sender_name or "").strip()
            or "ExtractAI"
        )

    def _transport(self) -> str:
        if self._gmail_ready():
            return "gmail_smtp"
        key = (self._settings.brevo_api_key or "").strip()
        if self._settings.brevo_use_smtp or key.startswith("xsmtpsib-"):
            return "brevo_smtp"
        if key:
            return "brevo_rest"
        return "none"

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        if not self._sender_email():
            logger.warning("mail.skipped_no_sender_email")
            return False

        transport = self._transport()
        if transport == "none":
            logger.warning("mail.skipped_no_credentials")
            return False

        text = text_body or "Please view this email in an HTML-capable client."

        try:
            if transport == "gmail_smtp":
                ok = await asyncio.to_thread(
                    self._send_gmail_smtp, to_email, subject, html_body, text
                )
            elif transport == "brevo_smtp":
                ok = await asyncio.to_thread(
                    self._send_brevo_smtp, to_email, subject, html_body, text
                )
            else:
                ok = await self._send_brevo_rest(to_email, subject, html_body, text)
            if ok:
                logger.info(
                    "mail.sent",
                    to=to_email,
                    subject=subject,
                    transport=transport,
                )
            return ok
        except Exception as exc:
            logger.exception(
                "mail.send_failed", to=to_email, error=str(exc), transport=transport
            )
            return False

    async def send_verification_email(
        self, *, to_email: str, verify_url: str, full_name: str | None = None
    ) -> bool:
        name = (full_name or "").strip() or "there"
        subject = "Verify your ExtractAI account"
        html = f"""
        <div style="font-family:Inter,Segoe UI,Arial,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0f172a">
          <p style="font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#0d9488;font-weight:700">ExtractAI</p>
          <h1 style="font-size:22px;margin:8px 0 16px">Confirm your email</h1>
          <p style="line-height:1.55;color:#334155">Hi {name},</p>
          <p style="line-height:1.55;color:#334155">
            Thanks for signing up. Open the button below <strong>once</strong> to verify your Gmail
            and unlock sign-in.
          </p>
          <p style="margin:28px 0">
            <a href="{verify_url}"
               style="background:#0d9488;color:#fff;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:600;display:inline-block">
              Verify email
            </a>
          </p>
          <p style="font-size:13px;color:#64748b;line-height:1.5">
            Or paste this link into your browser:<br/>
            <a href="{verify_url}" style="color:#0d9488;word-break:break-all">{verify_url}</a>
          </p>
          <p style="font-size:12px;color:#94a3b8;margin-top:32px">
            If you didn’t create an ExtractAI account, you can ignore this message.
          </p>
        </div>
        """
        text = (
            f"Hi {name},\n\n"
            f"Verify your ExtractAI account (one-time link):\n{verify_url}\n\n"
            "After verifying, you can sign in.\n"
            "If you didn’t sign up, ignore this email.\n"
        )
        return await self.send_email(
            to_email=to_email, subject=subject, html_body=html, text_body=text
        )

    def _build_message(
        self, to_email: str, subject: str, html_body: str, text_body: str
    ) -> MIMEMultipart:
        sender_email = self._sender_email()
        sender_name = self._sender_name()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((sender_name, sender_email))
        msg["To"] = to_email
        msg["Reply-To"] = sender_email
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        return msg

    def _send_gmail_smtp(
        self, to_email: str, subject: str, html_body: str, text_body: str
    ) -> bool:
        settings = self._settings
        login = (settings.smtp_user or settings.brevo_sender_email or "").strip()
        password = (settings.smtp_password or "").replace(" ", "").strip()
        host = (settings.smtp_host or "smtp.gmail.com").strip()
        port = int(settings.smtp_port or 587)
        sender_email = self._sender_email()
        msg = self._build_message(to_email, subject, html_body, text_body)

        with smtplib.SMTP(host, port, timeout=40) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(login, password)
            smtp.sendmail(sender_email, [to_email], msg.as_string())
        logger.info("mail.gmail_smtp_ok", host=host, port=port, from_email=sender_email)
        return True

    def _send_brevo_smtp(
        self, to_email: str, subject: str, html_body: str, text_body: str
    ) -> bool:
        settings = self._settings
        login = (settings.brevo_smtp_login or settings.brevo_sender_email or "").strip()
        password = (settings.brevo_api_key or "").strip()
        if not login:
            logger.error("mail.smtp_missing_login")
            return False

        sender_email = self._sender_email()
        msg = self._build_message(to_email, subject, html_body, text_body)

        hosts = [settings.brevo_smtp_host.strip() or "smtp-relay.brevo.com"]
        if "smtp-relay.brevo.com" not in hosts:
            hosts.append("smtp-relay.brevo.com")
        ports = [int(settings.brevo_smtp_port or 587), 587, 2525]
        seen_ports: list[int] = []
        for p in ports:
            if p not in seen_ports:
                seen_ports.append(p)

        last_error: Exception | None = None
        for host in hosts:
            for port in seen_ports:
                try:
                    with smtplib.SMTP(host, port, timeout=40) as smtp:
                        smtp.ehlo()
                        if port != 465:
                            smtp.starttls()
                            smtp.ehlo()
                        smtp.login(login, password)
                        smtp.sendmail(sender_email, [to_email], msg.as_string())
                    logger.info("mail.brevo_smtp_ok", host=host, port=port)
                    return True
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "mail.smtp_attempt_failed", host=host, port=port, error=str(exc)
                    )
        if last_error:
            raise last_error
        return False

    async def _send_brevo_rest(
        self, to_email: str, subject: str, html_body: str, text_body: str
    ) -> bool:
        settings = self._settings
        if not settings.brevo_api_key:
            logger.warning("mail.skipped_no_api_key")
            return False
        payload: dict[str, Any] = {
            "sender": {
                "name": self._sender_name(),
                "email": self._sender_email(),
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
            "textContent": text_body,
        }
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": settings.brevo_api_key.strip(),
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json=payload,
            )
        if resp.status_code >= 400:
            logger.error(
                "mail.brevo_api_error",
                status=resp.status_code,
                body=resp.text[:800],
            )
            return False
        logger.info("mail.brevo_api_ok", status=resp.status_code, body=resp.text[:200])
        return True

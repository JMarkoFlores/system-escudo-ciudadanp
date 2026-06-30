"""
Servicio de notificaciones push para alertas oficiales.
Soporta webhook HTTP, email SMTP y logging de fallback.
"""
import asyncio
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _split_emails(emails: Optional[str]) -> List[str]:
    if not emails:
        return []
    return [e.strip() for e in emails.split(",") if e.strip()]


async def _send_webhook(payload: Dict[str, Any]) -> bool:
    url = settings.ALERT_WEBHOOK_URL
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": "IntelExtorsion-Agent/1.0"},
            )
            response.raise_for_status()
        logger.info(f"Webhook de alerta enviado a {url}: status={response.status_code}")
        return True
    except Exception as exc:
        logger.warning(f"No se pudo enviar webhook de alerta: {exc}")
        return False


def _send_email_sync(
    subject: str,
    body_html: str,
    to_emails: List[str],
) -> bool:
    host = settings.ALERT_EMAIL_SMTP_HOST
    if not host:
        return False
    user = settings.ALERT_EMAIL_SMTP_USER
    password = settings.ALERT_EMAIL_SMTP_PASSWORD
    sender = settings.ALERT_EMAIL_FROM or user
    if not sender or not to_emails:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to_emails)
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, settings.ALERT_EMAIL_SMTP_PORT, timeout=15) as server:
            server.ehlo()
            if settings.ALERT_EMAIL_SMTP_PORT == 587:
                server.starttls()
                server.ehlo()
            if user and password:
                server.login(user, password)
            server.sendmail(sender, to_emails, msg.as_string())
        logger.info(f"Email de alerta enviado a {to_emails}")
        return True
    except Exception as exc:
        logger.warning(f"No se pudo enviar email de alerta: {exc}")
        return False


async def _send_email(subject: str, body_html: str, to_emails: List[str]) -> bool:
    if not settings.ALERT_EMAIL_SMTP_HOST or not to_emails:
        return False
    return await asyncio.to_thread(_send_email_sync, subject, body_html, to_emails)


def _build_email_body(payload: Dict[str, Any]) -> str:
    denuncia_id = payload.get("denuncia_id", "N/A")
    nivel = payload.get("nivel", "N/A")
    titulo = payload.get("titulo", "Alerta IntelExtorsión")
    descripcion = payload.get("descripcion", "")
    recomendacion = payload.get("recomendacion", "")
    tracking_code = payload.get("tracking_code", "N/A")
    tx_hash = payload.get("tx_hash", "N/A")
    timestamp = payload.get("timestamp", "")

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1e293b;">
        <h2 style="color: #dc2626;">🚨 Alerta IntelExtorsión — Nivel {nivel.upper()}</h2>
        <p><strong>Tracking ciudadano:</strong> {tracking_code}</p>
        <p><strong>Denuncia ID:</strong> {denuncia_id}</p>
        <p><strong>Título:</strong> {titulo}</p>
        <p><strong>Descripción:</strong> {descripcion}</p>
        <p><strong>Recomendación operativa:</strong> {recomendacion}</p>
        <p><strong>Tx Hash blockchain:</strong> {tx_hash}</p>
        <p><strong>Fecha:</strong> {timestamp}</p>
        <hr />
        <p style="font-size: 12px; color: #64748b;">
          Mensaje generado automáticamente por el sistema IntelExtorsión.<br/>
          Para denuncias formales ante la Fiscalía o PNP, el ciudadano debe usar la línea 111.
        </p>
      </body>
    </html>
    """


async def send_alert_notifications(
    denuncia_id: str,
    nivel: str,
    titulo: str,
    descripcion: str,
    recomendacion: Optional[str] = None,
    tracking_code: Optional[str] = None,
    tx_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Envía notificaciones push de una alerta por webhook y email.
    Nunca falla el flujo principal si las notificaciones fallan.
    """
    from datetime import datetime, timezone

    payload = {
        "event": "alerta_oficial",
        "denuncia_id": denuncia_id,
        "nivel": nivel,
        "titulo": titulo,
        "descripcion": descripcion,
        "recomendacion": recomendacion or "",
        "tracking_code": tracking_code or "N/A",
        "tx_hash": tx_hash or "N/A",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    results = {
        "webhook": await _send_webhook(payload),
        "email": False,
    }

    to_emails = _split_emails(settings.ALERT_EMAIL_TO)
    if to_emails:
        body = _build_email_body(payload)
        results["email"] = await _send_email(
            subject=f"[IntelExtorsión] Alerta {nivel.upper()}: {titulo}",
            body_html=body,
            to_emails=to_emails,
        )

    logger.info(f"Notificaciones push de alerta {denuncia_id}: {results}")
    return results

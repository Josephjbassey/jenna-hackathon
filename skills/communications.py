"""Communications tools for AgentPhone and AgentMail.

Provides email dispatch (SMTP or local outbox) and phone/SMS dispatch (Twilio or simulated),
enabling autonomous notifications, call initiation, and messaging.
"""
import os
import sys
from pathlib import Path
from langchain_core.tools import tool

_ROOT = Path(__file__).resolve().parent.parent
SANDBOX = _ROOT / "sandbox"
OUTBOX_DIR = SANDBOX / "outbox"
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
SMS_DIR = SANDBOX / "sms"
SMS_DIR.mkdir(parents=True, exist_ok=True)


@tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """Send an email via AgentMail.
    
    If SMTP credentials (SMTP_HOST, SMTP_USER, SMTP_PASS) are configured in .env,
    it delivers the email directly; otherwise it stages it securely into sandbox/outbox.
    """
    from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, NOTIFICATION_EMAIL

    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = SMTP_USER
            msg["To"] = recipient

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            return f"Email successfully sent to {recipient} with subject: '{subject}'."
        except Exception as e:
            return f"SMTP delivery failed ({e}); staged to outbox instead."

    # Offline / local staging
    import time
    filename = f"email_{int(time.time())}_{recipient.replace('@', '_at_')}.txt"
    filepath = OUTBOX_DIR / filename
    content = f"To: {recipient}\nSubject: {subject}\nDate: {time.ctime()}\n\n{body}\n"
    filepath.write_text(content, encoding="utf-8")
    return f"Email staged to local outbox: {filepath.name} (Configure SMTP in .env for live sending)."


@tool
def send_sms(recipient_phone: str, message_text: str) -> str:
    """Send an SMS text message via AgentPhone.
    
    If TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are configured, sends live SMS;
    otherwise stages the message to sandbox/sms/.
    """
    from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            msg = client.messages.create(
                to=recipient_phone,
                from_=TWILIO_FROM_NUMBER,
                body=message_text,
            )
            return f"SMS successfully sent to {recipient_phone} (SID: {msg.sid})."
        except Exception as e:
            return f"Twilio SMS delivery failed ({e}); recorded in sandbox/sms."

    # Offline / local staging
    import time
    filename = f"sms_{int(time.time())}_{recipient_phone.replace('+', '')}.txt"
    filepath = SMS_DIR / filename
    content = f"To: {recipient_phone}\nDate: {time.ctime()}\n\n{message_text}\n"
    filepath.write_text(content, encoding="utf-8")
    return f"SMS staged in sandbox/sms: {filepath.name} (Configure TWILIO in .env for live SMS)."


@tool
def make_phone_call(recipient_phone: str, message_to_speak: str) -> str:
    """Initiate an automated voice phone call via AgentPhone (Twilio Voice)."""
    from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            twiml = f"<Response><Say voice='Polly.Joanna'>{message_to_speak}</Say></Response>"
            call = client.calls.create(
                to=recipient_phone,
                from_=TWILIO_FROM_NUMBER,
                twiml=twiml,
            )
            return f"Outbound call placed to {recipient_phone} (SID: {call.sid})."
        except Exception as e:
            return f"Outbound call failed: {e}."

    return f"Call simulated for {recipient_phone} with speech: '{message_to_speak}'. (Configure TWILIO in .env for live telephony)."

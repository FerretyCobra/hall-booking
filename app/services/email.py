import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path

from ..config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SMTP_FROM, SMTP_USE_TLS, BASE_DIR
)
from ..database import SessionLocal
from .settings import get_setting

logger = logging.getLogger("app.email")

def send_email(to_email: str, subject: str, html_content: str, db=None):
    """Resilient email sender. Sends via SMTP if credentials/server are set,
    otherwise writes to data/emails.log for testing/development."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        host = get_setting(db, "smtp_host", SMTP_HOST)
        try:
            port = int(get_setting(db, "smtp_port", str(SMTP_PORT)))
        except ValueError:
            port = SMTP_PORT
        username = get_setting(db, "smtp_username", SMTP_USERNAME or "")
        password = get_setting(db, "smtp_password", SMTP_PASSWORD or "")
        from_addr = get_setting(db, "smtp_from", SMTP_FROM)
        use_tls = get_setting(db, "smtp_use_tls", str(SMTP_USE_TLS)).lower() in ("true", "1", "yes")
    finally:
        if close_db:
            db.close()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    
    part = MIMEText(html_content, "html")
    msg.attach(part)
    
    # Check if SMTP configuration is present/active (or fallback to console logging)
    use_smtp = True
    if host == "localhost" and port == 1025:
        # Dev SMTP server: check if open, otherwise log to file
        try:
            with smtplib.SMTP(host, port, timeout=2) as server:
                server.sendmail(from_addr, [to_email], msg.as_string())
            return
        except Exception:
            use_smtp = False
            
    if use_smtp:
        try:
            with smtplib.SMTP(host, port, timeout=5) as server:
                if use_tls:
                    server.starttls()
                if username and password:
                    server.login(username, password)
                server.sendmail(from_addr, [to_email], msg.as_string())
            return
        except Exception as e:
            logger.warning(f"SMTP sending failed, falling back to local file logging: {e}")
            
    # Fallback/dev mock: log to data/emails.log
    log_dir = BASE_DIR / "data"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "emails.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"TO: {to_email}\n")
        f.write(f"SUBJECT: {subject}\n")
        f.write("-" * 60 + "\n")
        f.write(html_content)
        f.write("\n" + "=" * 60 + "\n\n")

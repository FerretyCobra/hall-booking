"""Central configuration. Edit these to suit your site."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "hall_booking.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Secret used to sign the IT-dashboard session cookie.
# Set HALL_SECRET in the environment for production; the fallback is only for dev.
SECRET_KEY = os.environ.get("HALL_SECRET", "change-me-dev-secret-not-for-production")

# Bootstrap admin, created on first run if no users exist.
# Change the password immediately (or set env vars before first launch).
DEFAULT_ADMIN_USER = os.environ.get("HALL_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS = os.environ.get("HALL_ADMIN_PASS", "admin")

# Bookable window shown on the day-timeline grid, and the block size (minutes).
# Storage is still exact times; these only shape the picker UI / preset blocks.
DAY_START = "09:00"
DAY_END = "18:00"
SLOT_MINUTES = 30

# SMTP & Email Configurations
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", None)
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", None)
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@icmr-nitvar.res.in")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "False").lower() in ("true", "1", "yes")

DIRECTOR_EMAIL = os.environ.get("DIRECTOR_EMAIL", "director@icmr-nitvar.res.in")

# Department recipients
DEPARTMENT_EMAILS = {
    "housekeeping": os.environ.get("EMAIL_HOUSEKEEPING", "housekeeping@icmr-nitvar.res.in"),
    "it": os.environ.get("EMAIL_IT", "it-support@icmr-nitvar.res.in"),
    "stationery": os.environ.get("EMAIL_STATIONERY", "stationery@icmr-nitvar.res.in"),
    "canteen": os.environ.get("EMAIL_CANTEEN", "canteen@icmr-nitvar.res.in"),
}

# Automated Virtual Meeting Integrations (Zoom / Google Meet / Mock)
ACTIVE_MEETING_PROVIDER = os.environ.get("ACTIVE_MEETING_PROVIDER", "mock").lower()

# Zoom Credentials (Server-to-Server OAuth)
ZOOM_ACCOUNT_ID = os.environ.get("ZOOM_ACCOUNT_ID", "")
ZOOM_CLIENT_ID = os.environ.get("ZOOM_CLIENT_ID", "")
ZOOM_CLIENT_SECRET = os.environ.get("ZOOM_CLIENT_SECRET", "")

# Google Credentials (OAuth2 Refresh Token / Calendar API)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")

# Production & Session Security settings
PRODUCTION_MODE = os.environ.get("PRODUCTION_MODE", "False").lower() in ("true", "1", "yes")
SESSION_COOKIE_HTTPS_ONLY = os.environ.get("SESSION_COOKIE_HTTPS_ONLY", "False").lower() in ("true", "1", "yes")




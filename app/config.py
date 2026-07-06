"""Central configuration. Edit these to suit your site."""
import os
from pathlib import Path

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

from sqlalchemy.orm import Session
from ..models import SystemSetting

def get_setting(db: Session, key: str, default: str = "") -> str:
    """Load a system setting from DB. Fallback to default."""
    s = db.get(SystemSetting, key)
    if s is not None and s.value is not None:
        return s.value
    return default

def get_all_settings(db: Session) -> dict:
    """Retrieve all system settings as a dictionary."""
    rows = db.query(SystemSetting).all()
    return {r.key: r.value for r in rows}

def save_settings(db: Session, settings_dict: dict):
    """Batch save/update system settings."""
    for k, v in settings_dict.items():
        s = db.get(SystemSetting, k)
        if s is None:
            s = SystemSetting(key=k, value=str(v))
            db.add(s)
        else:
            s.value = str(v)
    db.commit()

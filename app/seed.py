"""First-run seed: creates the admin account, a few halls, and a starter
feature catalog (Microphone with types, Projector, Video conf). Safe to run
repeatedly; it only seeds when tables are empty."""
from .database import SessionLocal, engine, Base
from .models import User, Hall, FeatureCatalog, FeatureOption, HallFeature, DropdownConfig, SystemSetting
from .security import hash_password
from .config import DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASS, PRODUCTION_MODE


def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        # Check halls columns
        info = conn.exec_driver_sql("PRAGMA table_info(halls)").fetchall()
        cols = [row[1] for row in info]
        if "image" not in cols:
            conn.exec_driver_sql("ALTER TABLE halls ADD COLUMN image TEXT")
        if "requires_approval" not in cols:
            conn.exec_driver_sql("ALTER TABLE halls ADD COLUMN requires_approval BOOLEAN DEFAULT 0 NOT NULL")

        # Check bookings columns
        info_bookings = conn.exec_driver_sql("PRAGMA table_info(bookings)").fetchall()
        cols_bookings = [row[1] for row in info_bookings]
        if "coordinator_name" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN coordinator_name TEXT")
        if "coordinator_phone" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN coordinator_phone TEXT")
        if "coordinator_email" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN coordinator_email TEXT")
        if "approval_token" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN approval_token TEXT")
        if "virtual_meeting_requested" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN virtual_meeting_requested BOOLEAN DEFAULT 0 NOT NULL")
        if "meeting_link" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN meeting_link TEXT")
        if "reminder_sent" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN reminder_sent BOOLEAN DEFAULT 0 NOT NULL")
        if "stationery_requested" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN stationery_requested TEXT")
        if "food_requested" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN food_requested TEXT")
        if "housekeeping_requested" not in cols_bookings:
            conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN housekeeping_requested BOOLEAN DEFAULT 0 NOT NULL")

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            if PRODUCTION_MODE and DEFAULT_ADMIN_USER == "admin" and DEFAULT_ADMIN_PASS == "admin":
                raise RuntimeError(
                    "CRITICAL SECURITY ALERT: Booting in production mode with default admin credentials is prohibited. "
                    "Please configure unique values for HALL_ADMIN_USER and HALL_ADMIN_PASS in your environment."
                )
            db.add(User(username=DEFAULT_ADMIN_USER,
                        password_hash=hash_password(DEFAULT_ADMIN_PASS),
                        role="admin"))
            db.commit()

        if db.query(SystemSetting).count() == 0:
            _seed_system_settings(db)

        if db.query(DropdownConfig).count() == 0:
            _seed_dropdowns(db)
        else:
            # If DropdownConfig table already exists, verify we have stationery seeded
            if db.query(DropdownConfig).filter(DropdownConfig.category == "stationery").count() == 0:
                _seed_stationery(db)

        if db.query(Hall).count() == 0:
            _seed_sample(db)
    finally:
        db.close()


def _seed_system_settings(db):
    defaults = {
        "smtp_host": "localhost",
        "smtp_port": "1025",
        "smtp_username": "",
        "smtp_password": "",
        "smtp_from": "noreply@icmr-nitvar.res.in",
        "smtp_use_tls": "False",
        "director_email": "director@icmr-nitvar.res.in",
        "email_housekeeping": "housekeeping@icmr-nitvar.res.in",
        "email_it": "it-support@icmr-nitvar.res.in",
        "email_stationery": "stationery@icmr-nitvar.res.in",
        "email_canteen": "canteen@icmr-nitvar.res.in",
        "template_housekeeping": "<h2>Housekeeping Daily Schedule</h2>\n<p>Please find below the hall booking schedule for tomorrow (<strong>{date}</strong>) to assist with room setup and layout planning.</p>\n{table}",
        "template_it": "<h2>IT Support Daily Schedule</h2>\n<p>Please find below the hall booking schedule for tomorrow (<strong>{date}</strong>) detailing requested IT presence and hardware features.</p>\n{table}",
        "template_stationery": "<h2>Stationery Requirements Daily Schedule</h2>\n<p>Please find below the stationery and hardware requests for tomorrow's hall bookings (<strong>{date}</strong>).</p>\n{table}",
        "template_canteen": "<h2>Canteen Attendance Daily Schedule</h2>\n<p>Please find below the expected attendee counts and catering requests for tomorrow's meetings (<strong>{date}</strong>) to assist with canteen logistics and catering.</p>\n{table}"
    }
    for k, v in defaults.items():
        db.add(SystemSetting(key=k, value=v))
    db.commit()


def _seed_dropdowns(db):
    departments = [
        "Virology",
        "Epidemiology & Public Health",
        "Immunology",
        "Bioinformatics & Data Science",
        "Clinical Research",
        "Administration / Accounts",
        "Other Division"
    ]
    designations = [
        "Scientist G (Director)",
        "Scientist F",
        "Scientist E",
        "Scientist D",
        "Scientist C",
        "Scientist B",
        "Technical Officer",
        "Research Assistant",
        "Other Staff"
    ]
    
    for dept in departments:
        db.add(DropdownConfig(category="department", value=dept))
    for desig in designations:
        db.add(DropdownConfig(category="designation", value=desig))
    _seed_stationery(db, commit=False)
    db.commit()


def _seed_stationery(db, commit=True):
    items = ["Notepad", "Pen", "Pencil", "Marker", "Whiteboard eraser"]
    for item in items:
        db.add(DropdownConfig(category="stationery", value=item))
    if commit:
        db.commit()


def _seed_sample(db):
    # Feature catalog
    mic = FeatureCatalog(name="Microphone", value_type="multi_select")
    proj = FeatureCatalog(name="Projector", value_type="bool")
    vc = FeatureCatalog(name="Video conference", value_type="bool")
    db.add_all([mic, proj, vc])
    db.flush()

    mic_types = ["Handheld wireless", "Lavalier", "Gooseneck podium", "Headset"]
    opts = [FeatureOption(feature_id=mic.id, label=lbl, sort_order=i)
            for i, lbl in enumerate(mic_types)]
    db.add_all(opts)
    db.flush()

    halls = [
        Hall(name="Conference hall A", capacity=120),
        Hall(name="Meeting room 1", capacity=12),
        Hall(name="Training lab", capacity=30),
    ]
    db.add_all(halls)
    db.flush()

    # Hall A: 2 handheld + 1 lavalier mic, projector, video conf
    db.add_all([
        HallFeature(hall_id=halls[0].id, feature_id=mic.id, option_id=opts[0].id, quantity=2),
        HallFeature(hall_id=halls[0].id, feature_id=mic.id, option_id=opts[1].id, quantity=1),
        HallFeature(hall_id=halls[0].id, feature_id=proj.id, value="true"),
        HallFeature(hall_id=halls[0].id, feature_id=vc.id, value="true"),
        # Meeting room 1: projector only
        HallFeature(hall_id=halls[1].id, feature_id=proj.id, value="true"),
        # Training lab: gooseneck podium mic + projector
        HallFeature(hall_id=halls[2].id, feature_id=mic.id, option_id=opts[2].id, quantity=1),
        HallFeature(hall_id=halls[2].id, feature_id=proj.id, value="true"),
    ])
    db.commit()

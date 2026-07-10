"""First-run seed: creates the admin account, a few halls, and a starter
feature catalog (Microphone with types, Projector, Video conf). Safe to run
repeatedly; it only seeds when tables are empty."""
from .database import SessionLocal, engine, Base
from .models import User, Hall, FeatureCatalog, FeatureOption, HallFeature
from .security import hash_password
from .config import DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASS


def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        info = conn.exec_driver_sql("PRAGMA table_info(halls)").fetchall()
        cols = [row[1] for row in info]
        if "image" not in cols:
            conn.exec_driver_sql("ALTER TABLE halls ADD COLUMN image TEXT")
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(username=DEFAULT_ADMIN_USER,
                        password_hash=hash_password(DEFAULT_ADMIN_PASS),
                        role="admin"))
            db.commit()

        if db.query(Hall).count() == 0:
            _seed_sample(db)
    finally:
        db.close()


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

# Hall Booking

A LAN-hosted hall booking portal plus an IT dashboard. Users self-book a hall
for a time slot (BookMyShow-style day timeline); the IT team monitors bookings
and manages halls and their features.

Stack: **FastAPI + SQLite**, plain HTML/CSS/JS front-ends (no build step).

---

## Quick start

```bash
cd hall-booking
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Then open:

- Booking portal ..... http://localhost:8000/
- IT dashboard ....... http://localhost:8000/dashboard

From other machines on the LAN, replace `localhost` with the host machine's IP
(e.g. `http://192.168.1.20:8000/`).

**Default IT login:** `admin` / `admin` — change it immediately. Set your own
before first launch with environment variables:

```bash
export HALL_ADMIN_USER=itadmin
export HALL_ADMIN_PASS=a-strong-password
export HALL_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))")
python run.py
```

The database is created and seeded on first run at `data/hall_booking.db`
(3 sample halls + a Microphone / Projector / Video-conference feature catalog).
Delete that file to start clean.

---

## What the two apps do

**Booking portal** (no login — people just enter a name/dept):
filter by date, seats and required feature -> pick a hall -> pick a time on the
day-timeline grid (booked blocks show who has it) -> confirm -> get a cancel code.

**IT dashboard** (login required):
- Live bookings — auto-refreshing feed across all halls, with the booker's IP.
- Halls — add, rename (inline-edit), and archive. Archive is a soft-delete so
  past bookings keep their hall.
- Features — manage the catalog, the value type of each feature, and the option
  lists for select features (e.g. add a new mic type). Retiring an option is a
  soft-delete so halls using it aren't orphaned.
- Audit log — every create/cancel/admin change, with actor and IP.

---

## Project structure

```
hall-booking/
├── run.py                  Launcher (uvicorn on 0.0.0.0:8000)
├── requirements.txt
├── README.md
├── app/
│   ├── main.py             FastAPI app: middleware, routers, static mounts
│   ├── config.py           DB path, session secret, admin bootstrap, work hours
│   ├── database.py         Engine/session + SQLite WAL & BEGIN IMMEDIATE tuning
│   ├── models.py           ORM: halls, feature_catalog, feature_options,
│   │                       hall_features, bookings, users, audit_log
│   ├── schemas.py          Pydantic request/response shapes
│   ├── security.py         Password hashing + admin-session dependency
│   ├── seed.py             First-run seed (admin, sample halls & features)
│   ├── services/
│   │   ├── bookings.py     Overlap-safe create + cancel-by-code  <-- core logic
│   │   └── audit.py        Audit-log helper
│   └── routers/
│       ├── public.py       Halls list, availability, book, cancel (no login)
│       ├── auth.py         IT login / logout / me
│       ├── halls.py        IT hall CRUD
│       ├── features.py     IT catalog / options / hall assignment
│       └── dashboard.py    IT live bookings feed + audit
├── static/
│   ├── index.html          Booking portal
│   ├── dashboard.html      IT dashboard
│   ├── css/style.css
│   └── js/portal.js, dashboard.js
└── data/                   SQLite db created here at runtime
```

---

## The one part worth reading: double-booking safety

Because booking is instant and self-service, the only thing preventing two
people from grabbing the same slot is `app/services/bookings.py`. It does the
availability re-check and the insert inside a single transaction, and
`database.py` makes every transaction start with `BEGIN IMMEDIATE` (plus WAL and
a busy timeout). That takes the write lock *before* the "is it free?" check, so a
check-then-insert can't interleave with a competing request. The loser gets a
409 and the UI tells them to pick another slot. No seat-locking/hold system
needed at LAN scale.

Time is stored as `"HH:MM"` strings; the overlap test is
`existing.start < new.end AND existing.end > new.start`, which is correct for
same-day lexical comparison. The 30-minute grid is only a UI convenience — exact
times are stored, so odd durations still work.

---

## Notes / next steps

- CORS isn't configured because everything is same-origin (API + static served
  by one app). Keep it that way and it stays simple.
- For production-ish use, run behind a process manager (systemd, NSSM on
  Windows) and set the env vars above.
- Natural extensions: recurring bookings, email/WhatsApp confirmations,
  per-department booking limits, and an ICS export for calendars.
```

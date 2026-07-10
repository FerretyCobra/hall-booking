# ICMR-NITVAR Hall Booking System — Comprehensive Documentation

> **Version:** 1.0 | **Organization:** ICMR-NITVAR | **Stack:** Python / FastAPI / SQLite / Vanilla JS

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Directory Structure](#3-directory-structure)
4. [Technology Stack & Dependencies](#4-technology-stack--dependencies)
5. [Configuration Reference](#5-configuration-reference)
6. [Database Schema](#6-database-schema)
7. [API Reference](#7-api-reference)
8. [Services Layer](#8-services-layer)
9. [Front-End Applications](#9-front-end-applications)
10. [Booking Workflow Lifecycle](#10-booking-workflow-lifecycle)
11. [Email Notification System](#11-email-notification-system)
12. [Director Approval Workflow](#12-director-approval-workflow)
13. [Background Scheduler](#13-background-scheduler)
14. [Security Model](#14-security-model)
15. [Deployment Guide](#15-deployment-guide)
16. [Environment Variables Reference](#16-environment-variables-reference)
17. [Known Limitations & Future Work](#17-known-limitations--future-work)

---

## 1. Project Overview

The **ICMR-NITVAR Hall Booking System** is a lightweight, self-hosted web application that enables researchers, scientists, and administrative staff to book conference halls and meeting rooms at ICMR-NITVAR. The system removes the friction of manual scheduling (phone calls, emails, paper forms) and provides:

- A **public booking portal** accessible from any LAN device — no login required.
- A **private IT admin dashboard** for hall management, approval workflows, and configuration.
- **Automated email notifications** to departments (Housekeeping, IT Support, Stationery, Canteen).
- **Director-level approval** workflows for premium/restricted halls.
- **Virtual meeting link generation** (Zoom / Google Meet / Mock) upon booking confirmation.
- **Conflict-safe booking** with atomic database transactions to prevent double-booking.

### Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| No-login for bookers | Public API requires only name + department |
| Single-server simplicity | SQLite database, single Python process |
| Conflict safety | `BEGIN IMMEDIATE` transactions + lexical time comparison |
| Soft deletes | Halls use `active=False`; historical bookings preserved |
| Audit trail | Every state change written to `audit_log` |

---

## 2. Architecture Overview

```
Browser
├── Booking Portal (index.html / portal.js)
└── IT Admin Dashboard (dashboard.html / dashboard.js)
         │ HTTP REST
         ▼
FastAPI Application
├── Routers: public.py | auth.py | halls.py | features.py | dashboard.py
├── Services: bookings.py | notifications.py | email.py | meetings.py | settings.py | audit.py
└── Background Scheduler Thread (60s interval)
         │ SQLAlchemy ORM
         ▼
SQLite Database (WAL mode) — data/hall_booking.db
```

### Booking Creation Request Flow

```
User form submit
  → POST /api/bookings
  → Pydantic schema validation
  → bookings.create_booking()
      → BEGIN IMMEDIATE transaction
      → Validate hall exists & is active
      → find_conflict() — check overlapping confirmed bookings
      → Insert Booking row (confirmed | pending_approval)
      → If confirmed + virtual meeting → generate link
      → Audit log entry
      → COMMIT
  → Send email outside transaction
  → Return booking ID + cancel_code
```

---

## 3. Directory Structure

```
hall-booking/
├── run.py                      # Server entry point (uvicorn wrapper)
├── requirements.txt            # Python dependencies
├── todo.md                     # Feature task tracker
├── README.md                   # Quick-start guide
├── docs/
│   ├── DOCUMENTATION.md        # This file — comprehensive tech docs
│   └── SOP.md                  # Standard Operating Procedures
│
├── app/                        # FastAPI application package
│   ├── main.py                 # App factory, middleware, startup scheduler
│   ├── config.py               # Centralized configuration & env bindings
│   ├── database.py             # SQLAlchemy engine, session, transaction context
│   ├── models.py               # ORM models (declarative)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── security.py             # Password hashing, session auth guard
│   ├── seed.py                 # DB init and default data seeding
│   │
│   ├── routers/
│   │   ├── auth.py             # /api/auth/* — login, logout, credential change
│   │   ├── halls.py            # /api/admin/halls/* — CRUD for halls
│   │   ├── features.py         # /api/admin/features/* — feature catalog
│   │   ├── public.py           # /api/* — public booking endpoints
│   │   └── dashboard.py        # /api/admin/* — dashboard, approvals, audit
│   │
│   └── services/
│       ├── audit.py            # Audit log helper
│       ├── bookings.py         # Core booking lifecycle (create/cancel/update)
│       ├── email.py            # SMTP mailer with dev file fallback
│       ├── meetings.py         # Virtual meeting provider abstraction
│       ├── notifications.py    # Dept notifications, reminders, approval emails
│       └── settings.py         # Key/value system settings (DB-backed)
│
├── static/
│   ├── index.html              # Public booking portal (SPA)
│   ├── dashboard.html          # IT admin dashboard (SPA)
│   ├── css/style.css           # Shared stylesheet
│   ├── js/portal.js            # Portal logic
│   ├── js/dashboard.js         # Dashboard logic
│   └── images/                 # Uploaded hall images (auto-created)
│
└── data/
    ├── hall_booking.db          # SQLite database (WAL mode)
    └── emails.log               # Dev email fallback log
```

---

## 4. Technology Stack & Dependencies

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | FastAPI | >= 0.111 |
| ASGI Server | Uvicorn | >= 0.30 |
| ORM | SQLAlchemy | >= 2.0 |
| Database | SQLite (WAL) | bundled with Python |
| Password Hashing | Passlib (bcrypt) | >= 1.7 |
| Session Signing | Itsdangerous | >= 2.1 |
| File Uploads | python-multipart | >= 0.0.9 |
| Frontend | Vanilla HTML/CSS/JS | — |

**Why SQLite?** The system targets a single-server intranet deployment with low concurrency. SQLite with WAL mode handles concurrent reads alongside writes. The only critical race (double-booking) is handled with `BEGIN IMMEDIATE` transactions.

---

## 5. Configuration Reference

All configuration is in `app/config.py`. Every value can be overridden by an environment variable.

### File Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_DIR` | Project root | Auto-resolved |
| `DATA_DIR` | `<BASE_DIR>/data` | Database and log storage |
| `DB_PATH` | `<DATA_DIR>/hall_booking.db` | SQLite file path |
| `DATABASE_URL` | `sqlite:///...` | SQLAlchemy connection string |

### Security

| Variable | Env Var | Default | Notes |
|----------|---------|---------|-------|
| `SECRET_KEY` | `HALL_SECRET` | `"change-me-dev-secret"` | **Change in production!** |
| `DEFAULT_ADMIN_USER` | `HALL_ADMIN_USER` | `"admin"` | Bootstrap admin |
| `DEFAULT_ADMIN_PASS` | `HALL_ADMIN_PASS` | `"admin"` | **Change immediately!** |

### Booking Window

| Variable | Default | Description |
|----------|---------|-------------|
| `DAY_START` | `"09:00"` | Earliest bookable time in UI |
| `DAY_END` | `"18:00"` | Latest bookable time in UI |
| `SLOT_MINUTES` | `30` | Time grid slot size (UI only) |

### SMTP / Email

| Variable | Env Var | Default |
|----------|---------|---------|
| `SMTP_HOST` | `SMTP_HOST` | `"localhost"` |
| `SMTP_PORT` | `SMTP_PORT` | `1025` |
| `SMTP_USERNAME` | `SMTP_USERNAME` | `None` |
| `SMTP_PASSWORD` | `SMTP_PASSWORD` | `None` |
| `SMTP_FROM` | `SMTP_FROM` | `"noreply@icmr-nitvar.res.in"` |
| `SMTP_USE_TLS` | `SMTP_USE_TLS` | `False` |
| `DIRECTOR_EMAIL` | `DIRECTOR_EMAIL` | `"director@icmr-nitvar.res.in"` |

### Department Emails

| Department | Env Var | Default |
|------------|---------|---------|
| Housekeeping | `EMAIL_HOUSEKEEPING` | `"housekeeping@icmr-nitvar.res.in"` |
| IT Support | `EMAIL_IT` | `"it-support@icmr-nitvar.res.in"` |
| Stationery | `EMAIL_STATIONERY` | `"stationery@icmr-nitvar.res.in"` |
| Canteen | `EMAIL_CANTEEN` | `"canteen@icmr-nitvar.res.in"` |

> **Runtime override:** All SMTP and email settings can be updated at runtime via Admin Dashboard → Settings, stored in `system_settings` table.

---

## 6. Database Schema

### Entity Relationships

```
halls ──< hall_features >── feature_catalog ──< feature_options
halls ──< bookings
users (admin accounts only)
dropdown_configs (department / designation / stationery options)
audit_log
system_settings (key/value pairs)
```

### Table: `users`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `username` | STRING UNIQUE | Login username |
| `password_hash` | STRING | Bcrypt hash |
| `role` | STRING | Default: `"admin"` |
| `created_at` | DATETIME | UTC |

### Table: `halls`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `name` | STRING | Display name |
| `capacity` | INTEGER | Max occupants |
| `image` | STRING nullable | Filename in `static/images/` |
| `requires_approval` | BOOLEAN | Triggers director approval flow |
| `active` | BOOLEAN | Soft-delete flag |
| `created_at` | DATETIME | UTC |

### Table: `feature_catalog`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `name` | STRING UNIQUE | Feature type name (e.g., "Microphone") |
| `value_type` | STRING | `bool` / `number` / `text` / `single_select` / `multi_select` |
| `active` | BOOLEAN | Soft-delete |
| `created_at` | DATETIME | UTC |

### Table: `feature_options`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `feature_id` | INTEGER FK | → `feature_catalog.id` |
| `label` | STRING | Option display name |
| `active` | BOOLEAN | Soft-delete |
| `sort_order` | INTEGER | Display ordering |

### Table: `hall_features`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `hall_id` | INTEGER FK | → `halls.id` |
| `feature_id` | INTEGER FK | → `feature_catalog.id` |
| `option_id` | INTEGER FK nullable | → `feature_options.id` |
| `value` | STRING nullable | For bool/number/text features |
| `quantity` | INTEGER nullable | How many (e.g., 2 microphones) |

### Table: `bookings`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `hall_id` | INTEGER FK | → `halls.id` |
| `booking_date` | DATE | YYYY-MM-DD |
| `start_time` | STRING | `"HH:MM"` (24h) |
| `end_time` | STRING | `"HH:MM"` (24h) |
| `booked_by` | STRING | Requester's name |
| `dept` | STRING nullable | Requester's department |
| `purpose` | STRING nullable | Meeting title/purpose |
| `status` | STRING | `confirmed` / `pending_approval` / `cancelled` |
| `cancel_code` | STRING | 6-char self-cancel code |
| `created_at` | DATETIME | UTC |
| `created_ip` | STRING nullable | Requester's IP (accountability) |
| `coordinator_name` | STRING nullable | Meeting coordinator |
| `coordinator_phone` | STRING nullable | Coordinator phone |
| `coordinator_email` | STRING nullable | Coordinator email (for notifications) |
| `approval_token` | STRING nullable | Secure token for director approval links |
| `virtual_meeting_requested` | BOOLEAN | Was virtual link requested? |
| `meeting_link` | STRING nullable | Generated Zoom/Meet URL |
| `stationery_requested` | STRING nullable | Free-text stationery needs |
| `food_requested` | STRING nullable | Free-text catering needs |
| `support_staff_requested` | BOOLEAN | IT support staff needed |
| `housekeeping_requested` | BOOLEAN | Housekeeping needed |
| `scientist_designation` | STRING nullable | Scientist grade/title |
| `project_id` | STRING nullable | Associated project code |
| `attendees_count` | INTEGER nullable | Expected number of attendees |
| `features_requested` | TEXT nullable | AV/equipment requirements |

### Table: `dropdown_configs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `category` | STRING | `"department"` / `"designation"` / `"stationery"` |
| `value` | STRING | Option label |
| `active` | BOOLEAN | Visibility |

### Table: `audit_log`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto |
| `action` | STRING | e.g., `booking.create`, `hall.update` |
| `entity` | STRING | Table name |
| `entity_id` | INTEGER | Affected record PK |
| `actor` | STRING | Username or booker name |
| `actor_ip` | STRING | Client IP |
| `detail` | TEXT | Human-readable summary |
| `ts` | DATETIME | UTC |

### Table: `system_settings`

| Column | Type | Description |
|--------|------|-------------|
| `key` | STRING PK | Setting key |
| `value` | TEXT | Setting value |

**Known keys:** `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_from`, `smtp_use_tls`, `director_email`, `email_housekeeping`, `email_it`, `email_stationery`, `email_canteen`, `base_url`, `template_housekeeping`, `template_it`, `template_stationery`, `template_canteen`, `last_summary_notification_date`

---

## 7. API Reference

### 7.1 Public Booking API — `/api/*`

No authentication required.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/config` | Get UI config (hours, dropdowns) |
| `GET` | `/api/halls` | List active halls (filterable) |
| `GET` | `/api/halls/{id}/availability?on=<date>` | Get confirmed bookings for a hall/date |
| `POST` | `/api/bookings` | Create a new booking |
| `GET` | `/api/bookings/by-code?cancel_code=XXX` | Look up booking by cancel code |
| `POST` | `/api/bookings/by-code/cancel` | Cancel booking by cancel code |
| `POST` | `/api/bookings/by-code/update` | Update booking by cancel code |
| `GET` | `/api/bookings/approve-by-token?token=XXX` | Director approval confirmation page |
| `POST` | `/api/bookings/approve-by-token?token=XXX` | Director approves booking |
| `GET` | `/api/bookings/reject-by-token?token=XXX` | Director rejection confirmation page |
| `POST` | `/api/bookings/reject-by-token?token=XXX` | Director rejects booking |

#### BookingIn Schema (POST /api/bookings)

```json
{
  "hall_id": 1,
  "booking_date": "2026-07-15",
  "start_time": "10:00",
  "end_time": "11:30",
  "booked_by": "Dr. Sharma",
  "dept": "Research",
  "purpose": "Project Review",
  "attendees_count": 20,
  "coordinator_name": "Mr. Kumar",
  "coordinator_phone": "9876543210",
  "coordinator_email": "kumar@icmr.res.in",
  "support_staff_requested": false,
  "housekeeping_requested": true,
  "virtual_meeting_requested": false,
  "stationery_requested": "Notebooks x5, Pens x10",
  "food_requested": "Tea & Snacks for 20",
  "scientist_designation": "Scientist-C",
  "project_id": "PROJ-2026-001",
  "features_requested": "Projector + Microphone"
}
```

**Success:** `{"id": 42, "cancel_code": "XK7MQP", "status": "confirmed", ...}`

**Errors:** `409 Conflict` (slot taken) | `422` (validation failure)

### 7.2 Authentication API — `/api/auth/*`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/login` | None | Log in, sets session cookie |
| `POST` | `/api/auth/logout` | Session | Clear session |
| `GET` | `/api/auth/me` | Session | Get current user |
| `POST` | `/api/auth/credentials` | Session | Change username/password |

### 7.3 Admin — Halls — `/api/admin/halls/*`

Requires admin session.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/halls` | List all halls |
| `POST` | `/api/admin/halls` | Create hall |
| `PATCH` | `/api/admin/halls/{id}` | Update hall |
| `POST` | `/api/admin/halls/{id}/picture` | Upload hall image |

### 7.4 Admin — Features — `/api/admin/features/*`

Requires admin session.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/features` | List feature catalog |
| `POST` | `/api/admin/features` | Create feature type |
| `PATCH` | `/api/admin/features/{id}` | Update/retire feature |
| `POST` | `/api/admin/features/{id}/options` | Add option to feature |
| `PATCH` | `/api/admin/features/options/{id}` | Update/retire option |
| `GET` | `/api/admin/features/hall/{id}` | Features assigned to hall |
| `POST` | `/api/admin/features/hall/{id}` | Assign feature to hall |
| `DELETE` | `/api/admin/features/hall/assignment/{id}` | Remove assignment |

**Feature value types:** `bool` / `number` / `text` / `single_select` / `multi_select`

### 7.5 Admin — Dashboard — `/api/admin/*`

Requires admin session.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/bookings` | All bookings (filter: `on`, `status`) |
| `POST` | `/api/admin/bookings/{id}/approve` | Approve pending booking |
| `POST` | `/api/admin/bookings/{id}/reject` | Reject pending booking |
| `GET` | `/api/admin/dropdowns` | List dropdown configs |
| `POST` | `/api/admin/dropdowns` | Add dropdown option |
| `DELETE` | `/api/admin/dropdowns/{id}` | Remove dropdown option |
| `POST` | `/api/admin/trigger-notifications` | Manually send dept notifications |
| `GET` | `/api/admin/audit` | Audit log (max 500 rows) |
| `GET` | `/api/admin/settings` | All system settings |
| `POST` | `/api/admin/settings` | Batch update settings |

---

## 8. Services Layer

### 8.1 Booking Service (`app/services/bookings.py`)

**`create_booking(db, data, ip)`** — Main booking function:
1. Validates `HH:MM` time format and `end > start`.
2. Opens `BEGIN IMMEDIATE` transaction (write-locks SQLite).
3. Verifies hall exists and is active.
4. Calls `find_conflict()` — checks overlapping `confirmed` bookings.
5. Sets status: `pending_approval` if hall requires approval, else `confirmed`.
6. Generates 6-char cancel code from unambiguous 31-char alphabet.
7. Inserts booking; generates meeting link if confirmed + virtual requested.
8. Commits, then sends email notifications outside the transaction.

**`cancel_booking(db, booking_id, code, ip)`** — Validates cancel code, sets `"cancelled"`.

**`update_booking(db, booking_id, cancel_code, data, ip)`** — Full re-validation with conflict check excluding the current booking.

**`find_conflict(db, hall_id, date, start, end, exclude_id)`** — Overlap test:
```
existing.start_time < end AND existing.end_time > start
```
Works because `"HH:MM"` strings have correct lexical ordering.

### 8.2 Notification Service (`app/services/notifications.py`)

| Function | Trigger | Recipient |
|----------|---------|-----------|
| `send_department_notifications()` | Daily at 18:00 | Housekeeping, IT, Stationery, Canteen |
| `send_upcoming_reminders()` | Every 60s | IT, Housekeeping (for meetings in 15min) |
| `send_director_approval_request()` | On pending_approval creation | Director's Office |
| `send_booking_confirmation()` | On booking confirmed | Coordinator |
| `send_booking_rejection()` | On booking rejected | Coordinator |

### 8.3 Email Service (`app/services/email.py`)

Resilient `send_email(to, subject, html, db)`:
1. Reads SMTP config from DB (runtime settings) with fallback to `config.py`.
2. If `host=localhost, port=1025` → tries local MailHog.
3. On any SMTP failure → appends to `data/emails.log`.

### 8.4 Virtual Meeting Service (`app/services/meetings.py`)

Strategy pattern — selected via `ACTIVE_MEETING_PROVIDER` env var:

| Provider | Env Value | Behavior |
|----------|-----------|---------|
| `MockMeetingProvider` | `"mock"` (default) | `https://meet.mock.com/room/<uuid>` |
| `ZoomMeetingProvider` | `"zoom"` | Stub for Zoom S2S OAuth |
| `GoogleMeetProvider` | `"google"` | Stub for Google Calendar API |

### 8.5 Settings Service (`app/services/settings.py`)

`get_setting(db, key, default)` / `get_all_settings(db)` / `save_settings(db, dict)`

Backed by `system_settings` table. Allows runtime overrides without server restart.

### 8.6 Audit Service (`app/services/audit.py`)

`audit.log(db, action, entity, entity_id, actor, actor_ip, detail)`

All create/update/delete/approve/reject actions write to `audit_log`.

---

## 9. Front-End Applications

### 9.1 Public Booking Portal (`/`)

Views: Hall Selection → Date Picker → Time Grid → Booking Form → Receipt / Manage Booking

- No authentication required.
- Time grid visualizes booked/free slots from `/api/halls/{id}/availability`.
- Cancel code stored in `sessionStorage` for manage-booking flow.

### 9.2 IT Admin Dashboard (`/dashboard`)

Tabs: Live Bookings | Pending Approvals | Hall Management | Feature Catalog | Dropdown Config | Email Settings | System Settings | Audit Log | Account Settings

- Session-cookie authentication.
- All state changes via REST API calls.

---

## 10. Booking Workflow Lifecycle

```
Submit booking
     │
     ├─ hall.requires_approval = False ──► status = "confirmed"
     │                                         │
     │                               ◄──────────┤ (if virtual meeting requested)
     │                              Generate meeting link
     │                                         │
     │                                  Send confirmation
     │                                  email to coordinator
     │
     └─ hall.requires_approval = True ──► status = "pending_approval"
                                               │
                                    Send approval email to Director
                                               │
                                    Director clicks Approve/Reject
                                               │
                             ┌─────────────────┴──────────────────┐
                             ▼                                    ▼
                      status = "confirmed"               status = "cancelled"
                      + meeting link                     Rejection email
                      + confirmation email               to coordinator
```

**Cancellation:** Either the booker (via cancel code at portal) or an admin (from dashboard) can cancel any confirmed/pending booking.

---

## 11. Email Notification System

### Daily Department Summary

- Fires at/after 18:00, guarded by `last_summary_notification_date` setting.
- Sends tailored HTML tables to each department for tomorrow's bookings.
- Templates are DB-configurable; support `{date}` and `{table}` placeholders.

**What each department receives:**

| Department | Condition | Content |
|------------|-----------|---------|
| Housekeeping | All bookings | Hall, timings, attendees, HK flag, coordinator |
| IT Support | All bookings | Hall, timings, IT flag, features, virtual link, coordinator |
| Stationery | `stationery_requested` not empty | Hall, timings, features, stationery items |
| Canteen | `food_requested` not empty | Hall, timings, attendees, catering description |

### 15-Minute Pre-Meeting Reminders

- Checked every 60s; fires when a meeting with IT/HK support starts within 15 minutes.
- In-memory `SENT_REMINDERS` set prevents duplicate alerts per session.

---

## 12. Director Approval Workflow

1. Booking for an approval-required hall → `pending_approval` status + secure token.
2. Email sent to Director with approve/reject buttons (token-authenticated URLs).
3. Director clicks → token endpoint processes request (no login needed).
4. Approval: booking confirmed, meeting link generated, coordinator notified.
5. Rejection: booking cancelled, coordinator notified.
6. **Idempotent:** Re-clicking a processed token shows a status notice, no re-processing.

---

## 13. Background Scheduler

Started in `@app.on_event("startup")` as a daemon thread. Runs every 60 seconds:

```
Every 60s:
  if current_hour >= 18 AND last_run != today:
      send_department_notifications()
      save last_run = today
  send_upcoming_reminders()
```

Each iteration opens and closes its own DB session in a try/finally block.

---

## 14. Security Model

| Concern | Mitigation |
|---------|-----------|
| Admin auth | Session cookie signed by `SECRET_KEY` (Itsdangerous via Starlette) |
| Password storage | bcrypt via Passlib |
| Double-booking race | `BEGIN IMMEDIATE` SQLite transaction |
| Director approval | Cryptographically random 16-byte URL-safe token |
| Booker accountability | Client IP captured and stored on all bookings |
| Cancel code security | 6-char from 31-char alphabet ≈ 887M combinations |
| SQL injection | SQLAlchemy ORM parameterized queries throughout |
| File uploads | Content-type check + extension whitelist + deterministic filenames |

**Production checklist:**
- Set `HALL_SECRET` to a long random string.
- Change default admin password at first login.
- Configure all `SMTP_*` environment variables.
- Set `base_url` in System Settings to the server's actual LAN IP/hostname.

---

## 15. Deployment Guide

### Prerequisites

- Python 3.10+
- Windows or Linux server on LAN
- SMTP mail server (institutional or relay)

### First-Time Setup

```powershell
# 1. Navigate to project
cd D:\Work\Projects\hall-booking

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
$env:HALL_SECRET = "your-very-long-random-secret"
$env:HALL_ADMIN_PASS = "YourStrongPassword"
$env:SMTP_HOST = "smtp.icmr-nitvar.res.in"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "noreply@icmr-nitvar.res.in"
$env:SMTP_PASSWORD = "your-smtp-password"
$env:SMTP_USE_TLS = "true"

# 5. Start server
python run.py
```

Access: `http://<server-ip>:8000/` (portal) and `http://<server-ip>:8000/dashboard` (admin)

### Running as a Windows Service (NSSM)

```
nssm install HallBooking "D:\Work\Projects\hall-booking\.venv\Scripts\python.exe"
nssm set HallBooking AppDirectory "D:\Work\Projects\hall-booking"
nssm set HallBooking AppParameters "run.py"
nssm set HallBooking AppEnvironmentExtra "HALL_SECRET=..." "HALL_ADMIN_PASS=..."
nssm start HallBooking
```

### Database Backup

```powershell
# Safe online backup
sqlite3 data\hall_booking.db ".backup data\backup.db"

# Offline copy
copy data\hall_booking.db "backups\hall_booking_$(Get-Date -Format 'yyyyMMdd').db"
```

---

## 16. Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `HALL_SECRET` | Session signing key | `"abc123...xyz"` |
| `HALL_ADMIN_USER` | Default admin username | `"admin"` |
| `HALL_ADMIN_PASS` | Default admin password | `"SecurePass123"` |
| `SMTP_HOST` | Mail server | `"smtp.gmail.com"` |
| `SMTP_PORT` | Mail port | `"587"` |
| `SMTP_USERNAME` | Mail auth user | `"noreply@domain.in"` |
| `SMTP_PASSWORD` | Mail auth password | `"mailpassword"` |
| `SMTP_FROM` | Sender address | `"noreply@icmr-nitvar.res.in"` |
| `SMTP_USE_TLS` | Enable STARTTLS | `"true"` |
| `DIRECTOR_EMAIL` | Director email | `"director@icmr-nitvar.res.in"` |
| `EMAIL_HOUSEKEEPING` | Housekeeping email | `"housekeeping@icmr-nitvar.res.in"` |
| `EMAIL_IT` | IT support email | `"it-support@icmr-nitvar.res.in"` |
| `EMAIL_STATIONERY` | Stationery email | `"stationery@icmr-nitvar.res.in"` |
| `EMAIL_CANTEEN` | Canteen email | `"canteen@icmr-nitvar.res.in"` |
| `ACTIVE_MEETING_PROVIDER` | Meeting link provider | `"mock"` / `"zoom"` / `"google"` |

---

## 17. Known Limitations & Future Work

### Current Limitations

| Area | Limitation |
|------|-----------|
| Reminder deduplication | `SENT_REMINDERS` is in-memory; clears on server restart |
| Admin accounts | Single admin account only |
| Meeting providers | Zoom/Google Meet are stubs; need real API credentials |
| Timezone | All times in server local time; no timezone support |
| Recurring bookings | Not supported; each session booked individually |
| Data export | No CSV/PDF export from dashboard |
| Capacity enforcement | API does not block `attendees_count > hall.capacity` |
| Past date bookings | API does not reject past dates |
| Cancellation email | No email sent on public self-cancellation |

### Planned Enhancements

- Multi-admin role support
- Real Zoom / Google Meet API integration
- CSV/PDF report export
- Past date validation
- Cancellation notification emails
- Recurring booking support
- Timezone-aware scheduling
- Attendee count vs. capacity enforcement

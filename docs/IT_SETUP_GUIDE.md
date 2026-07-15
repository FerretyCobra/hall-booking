# IT Setup Guide — ICMR-NITVAR Hall Booking System
### Intranet / Local Deployment — Step-by-Step for IT Staff

> **Audience:** IT personnel responsible for deploying and maintaining the hall booking server
> **Scope:** Windows server on a local area network (LAN / intranet)
> **Time to complete first-time setup:** ~30–45 minutes

---

## Table of Contents

1. [What You're Setting Up](#1-what-youre-setting-up)
2. [Prerequisites Checklist](#2-prerequisites-checklist)
3. [Step 1 — Install Python](#3-step-1--install-python)
4. [Step 2 — Copy the Project Files](#4-step-2--copy-the-project-files)
5. [Step 3 — Create the Virtual Environment](#5-step-3--create-the-virtual-environment)
6. [Step 4 — Install Dependencies](#6-step-4--install-dependencies)
7. [Step 5 — Configure Environment Variables](#7-step-5--configure-environment-variables)
8. [Step 6 — First Run & Verify](#8-step-6--first-run--verify)
9. [Step 7 — Configure the System via Admin Dashboard](#9-step-7--configure-the-system-via-admin-dashboard)
10. [Step 8 — Open Firewall Port](#10-step-8--open-firewall-port)
11. [Step 9 — Run as a Windows Service (NSSM)](#11-step-9--run-as-a-windows-service-nssm)
12. [Step 10 — Test from Another Machine](#12-step-10--test-from-another-machine)
13. [Step 11 — Configure SMTP Email](#13-step-11--configure-smtp-email)
14. [Step 12 — Seed Your Real Data](#14-step-12--seed-your-real-data)
15. [Step 13 — Announce the URL to Staff](#15-step-13--announce-the-url-to-staff)
16. [Ongoing Maintenance](#16-ongoing-maintenance)
17. [Uninstall / Teardown](#17-uninstall--teardown)
18. [Quick Troubleshooting Reference](#18-quick-troubleshooting-reference)

---

## 1. What You're Setting Up

```
┌──────────────────────────────────────────┐
│           Your LAN / Intranet            │
│                                          │
│   [Any staff browser]                    │
│       http://192.168.x.x:8000/           │
│            │                             │
│            │ HTTP                        │
│            ▼                             │
│   ┌─────────────────────┐                │
│   │  Hall Booking       │ ← This server  │
│   │  Server (Python)    │                │
│   │  Port 8000          │                │
│   │  D:\HallBooking\    │                │
│   └─────────────────────┘                │
│            │                             │
│            │ SMTP                        │
│            ▼                             │
│   [Institution mail server]              │
└──────────────────────────────────────────┘
```

The server machine runs a Python web application that all other machines on the LAN access through a browser. **No software installation is needed on staff computers** — just a browser.

---

## 2. Prerequisites Checklist

Before you start, confirm the following:

| Item | Requirement | How to Check |
|------|-------------|--------------|
| **Operating System** | Windows 10/11 or Windows Server 2016+ | `winver` in Run dialog |
| **Python** | Version 3.10 or higher | `python --version` in cmd |
| **Available Port** | Port 8000 free on the server | `netstat -ano \| findstr :8000` |
| **Disk Space** | At least 500 MB free | Check drive properties |
| **LAN access** | Server reachable from other PCs | Ping from another machine |
| **SMTP server** | Institution mail relay available | Ask your mail admin |
| **Static IP** | Server machine has a fixed LAN IP | Check network settings |

> 💡 **Tip:** Give the server machine a static IP address (e.g., `192.168.1.10`) before starting. Otherwise the URL you tell staff could change after a DHCP lease renewal.

---

## 3. Step 1 — Install Python

### Check if Python is already installed

Open **Command Prompt** (`Win + R` → type `cmd` → Enter):

```cmd
python --version
```

If you see `Python 3.10.x` or higher, skip to Step 2.

### Install Python (if not installed)

1. Go to https://www.python.org/downloads/
2. Download **Python 3.11** (recommended) — Windows installer (64-bit)
3. Run the installer
4. ✅ **IMPORTANT:** Check **"Add Python to PATH"** at the bottom of the installer before clicking Install
5. Click **"Install Now"**

### Verify installation

```cmd
python --version
pip --version
```

Both should return version numbers without errors.

---

## 4. Step 2 — Copy the Project Files

Choose a permanent home for the application on the server. A clean, accessible path is recommended:

```
D:\HallBooking\
```

Or if you prefer:
```
C:\Apps\HallBooking\
```

### If you have the project as a ZIP file:

1. Extract the ZIP to `D:\HallBooking\`
2. Verify the structure looks like this:

```
D:\HallBooking\
├── run.py
├── requirements.txt
├── app\
├── static\
└── data\
```

### If copying from another PC on the network:

```cmd
xcopy \\source-pc\shared\hall-booking D:\HallBooking /E /I /H
```

---

## 5. Step 3 — Create the Virtual Environment

A virtual environment isolates the project's Python packages from the rest of the system. This is important so that system-wide Python updates don't break the app.

Open Command Prompt **as Administrator** and run:

```cmd
cd D:\HallBooking
python -m venv .venv
```

You should now see a `.venv` folder inside `D:\HallBooking\`.

### Activate the virtual environment

```cmd
.venv\Scripts\activate
```

Your prompt will change to show `(.venv)` at the start — this means you're inside the virtual environment.

> ℹ️ You only need to activate the virtual environment manually when running commands. The Windows Service will handle this automatically once configured.

---

## 6. Step 4 — Install Dependencies

With the virtual environment **activated**, run:

```cmd
pip install -r requirements.txt
```

You will see packages being downloaded and installed. This takes 1–3 minutes depending on internet speed.

**Expected packages installed:**
- `fastapi` — web framework
- `uvicorn` — ASGI web server
- `sqlalchemy` — database ORM
- `passlib` — password hashing
- `itsdangerous` — session signing
- `python-multipart` — file upload support

### Verify installation

```cmd
pip list
```

You should see all the above packages listed.

---

## 7. Step 5 — Configure Environment Variables

Environment variables hold sensitive configuration (passwords, secret keys) outside the code files, so they're not accidentally shared or committed.

### Generate a secure secret key

In the activated virtual environment, run:

```cmd
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output — it will look like:
```
a3f8d92bc014e7a1c6f3b8e0d4952a7f1b6c4e8d2a0f5c9b3e7d1a4f8c2b6e0
```

### Create the environment setup script

Create a file called `set_env.bat` in `D:\HallBooking\`:

```bat
@echo off
REM Hall Booking System — Environment Variables
REM Edit these values before running for the first time.
REM Keep this file PRIVATE — do not share it or put it in version control.

REM === SECURITY ===
set HALL_SECRET=PASTE_YOUR_GENERATED_SECRET_HERE
set HALL_ADMIN_USER=admin
set HALL_ADMIN_PASS=ChangeThisNow123

REM === SMTP EMAIL (get these from your mail admin) ===
set SMTP_HOST=smtp.icmr-nitvar.res.in
set SMTP_PORT=587
set SMTP_USERNAME=noreply@icmr-nitvar.res.in
set SMTP_PASSWORD=your-smtp-password-here
set SMTP_FROM=noreply@icmr-nitvar.res.in
set SMTP_USE_TLS=true

REM === DEPARTMENT EMAILS ===
set DIRECTOR_EMAIL=director@icmr-nitvar.res.in
set EMAIL_HOUSEKEEPING=housekeeping@icmr-nitvar.res.in
set EMAIL_IT=it-support@icmr-nitvar.res.in
set EMAIL_STATIONERY=stationery@icmr-nitvar.res.in
set EMAIL_CANTEEN=canteen@icmr-nitvar.res.in

REM === VIRTUAL MEETING PROVIDER ===
REM Options: mock (default), zoom, google
set ACTIVE_MEETING_PROVIDER=mock

REM Zoom S2S OAuth (Optional, required if ACTIVE_MEETING_PROVIDER=zoom)
set ZOOM_ACCOUNT_ID=your_zoom_account_id_here
set ZOOM_CLIENT_ID=your_zoom_client_id_here
set ZOOM_CLIENT_SECRET=your_zoom_client_secret_here

REM Google OAuth2 (Optional, required if ACTIVE_MEETING_PROVIDER=google)
set GOOGLE_CLIENT_ID=your_google_client_id_here
set GOOGLE_CLIENT_SECRET=your_google_client_secret_here
set GOOGLE_REFRESH_TOKEN=your_google_refresh_token_here

```

> ⚠️ Replace every placeholder value with real values before proceeding.

> ⚠️ Paste your generated secret key into `HALL_SECRET=`.

---

## 8. Step 6 — First Run & Verify

### Run the server for the first time

```cmd
cd D:\HallBooking
set_env.bat
.venv\Scripts\activate
python run.py
```

You should see output like:

```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Verify it works

Open a browser **on the same machine** and go to:

- **Booking Portal:** http://localhost:8000/
- **Admin Dashboard:** http://localhost:8000/dashboard

Both pages should load without errors.

### What happened in the background (first run)

The application automatically:
1. Created the SQLite database at `D:\HallBooking\data\hall_booking.db`
2. Created all database tables
3. Created the default admin account (`admin` / `admin`)
4. Seeded 3 sample halls (Conference Hall A, Meeting Room 1, Training Lab)
5. Seeded a starter feature catalog (Microphone, Projector, Video Conference)
6. Seeded default dropdown options (departments, designations, stationery items)
7. Saved default email settings to the database

### Stop the server for now

Press `Ctrl + C` in the command prompt to stop it. We'll configure it properly before making it permanent.

---

## 9. Step 7 — Configure the System via Admin Dashboard

Now that the server runs, configure it through the admin dashboard before going live.

### 9.1 Log in

1. Open http://localhost:8000/dashboard
2. Log in with: `admin` / `admin`

### 9.2 Change the Admin Password IMMEDIATELY

1. Go to **Account Settings** tab
2. Enter a new **Username** (or keep `admin`)
3. Enter a strong new **Password** (minimum 12 characters, mix of letters, numbers, symbols)
4. Click **Save Credentials**
5. Log in again with your new credentials

### 9.3 Set the Base URL

This is critical — it makes the Director's approval email links work correctly.

1. Go to **Settings** tab
2. Find `base_url`
3. Set it to: `http://192.168.x.x:8000` (use the actual LAN IP of this server)
   - To find the server's IP: open cmd → type `ipconfig` → look for IPv4 Address under your network adapter
   - Example: `http://192.168.1.10:8000`
4. Click **Save Settings**

### 9.4 Configure Department Email Addresses

1. In the **Settings** tab, update each email address:

   | Setting Key | Set to |
   |-------------|--------|
   | `director_email` | Director's actual email address |
   | `email_housekeeping` | Housekeeping team's actual email |
   | `email_it` | IT team's actual email |
   | `email_stationery` | Stationery store's actual email |
   | `email_canteen` | Canteen team's actual email |

2. Click **Save Settings**

### 9.5 Configure SMTP Settings

1. In the **Settings** tab, set:

   | Setting | Value |
   |---------|-------|
   | `smtp_host` | Your mail server (e.g., `smtp.icmr-nitvar.res.in`) |
   | `smtp_port` | Port number (usually `587` for TLS, `25` for plain) |
   | `smtp_username` | Email auth username |
   | `smtp_password` | Email auth password |
   | `smtp_from` | The "from" address staff will see |
   | `smtp_use_tls` | `true` or `false` |

2. Click **Save Settings**

### 9.6 Add Real Halls

The seeded halls are samples. Replace them with your actual halls.

1. Go to **Hall Management** tab
2. For each sample hall you don't need: click **Edit** → toggle **Active** to OFF → **Save**
3. Click **+ Add Hall** and fill in your actual halls:
   - Name (e.g., "Seminar Hall", "Director's Conference Room")
   - Capacity (maximum occupants)
   - Requires Director Approval: ✅ check this for premium/restricted halls
4. Upload a photo for each hall (optional but recommended)

### 9.7 Configure Hall Features

1. Go to **Feature Catalog** tab
2. Review the seeded features (Microphone, Projector, Video Conference) — edit or keep them
3. Add any additional features your halls have (e.g., "Whiteboard", "Air Conditioning", "PA System")
4. For each hall, assign its actual features under **Hall Management** → select hall → Features section

### 9.8 Update Dropdown Options

1. Go to **Dropdown Config** tab
2. Update the **Department** list to match your actual institute divisions
3. Update the **Designation** list to match your actual designations/grades
4. Update the **Stationery** list to match items available from your store

---

## 10. Step 8 — Open Firewall Port

Other machines on the LAN need to reach port 8000. By default, Windows Firewall blocks inbound connections on non-standard ports.

### Open port 8000 in Windows Firewall

Open **Command Prompt as Administrator** and run:

```cmd
netsh advfirewall firewall add rule ^
  name="Hall Booking System" ^
  dir=in ^
  action=allow ^
  protocol=TCP ^
  localport=8000
```

### Verify from another machine

From a different computer on the same LAN, open a browser and go to:
```
http://192.168.x.x:8000/
```
(Replace `192.168.x.x` with the server's actual IP.)

If you can see the booking portal, the firewall is configured correctly.

### If staff are on a different subnet (VLAN)

Talk to your network administrator to allow routing between the server's VLAN and the staff VLAN on port 8000.

---

## 11. Step 9 — Run as a Windows Service (NSSM)

Running `python run.py` manually means the server stops when you close the command prompt or log out. To make it run continuously — automatically on startup — use **NSSM** (Non-Sucking Service Manager), a free Windows utility.

### Download NSSM

1. Go to https://nssm.cc/download
2. Download the latest release ZIP
3. Extract it — you'll get `nssm-2.24\win64\nssm.exe` (or similar)
4. Copy `nssm.exe` to `D:\HallBooking\` for convenience (or anywhere in your PATH)

### Install the service

Open **Command Prompt as Administrator**:

```cmd
cd D:\HallBooking
nssm install HallBookingSystem
```

A GUI window will open. Fill in the tabs:

#### Application tab:
| Field | Value |
|-------|-------|
| **Path** | `D:\HallBooking\.venv\Scripts\python.exe` |
| **Startup directory** | `D:\HallBooking` |
| **Arguments** | `run.py` |

#### Details tab:
| Field | Value |
|-------|-------|
| **Display name** | `Hall Booking System` |
| **Description** | `ICMR-NITVAR Hall Booking Web Application` |
| **Startup type** | `Automatic` |

#### Environment tab (add each line separately):
```
HALL_SECRET=your-very-long-random-secret-here
HALL_ADMIN_USER=admin
HALL_ADMIN_PASS=YourChosenPassword123
SMTP_HOST=smtp.icmr-nitvar.res.in
SMTP_PORT=587
SMTP_USERNAME=noreply@icmr-nitvar.res.in
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@icmr-nitvar.res.in
SMTP_USE_TLS=true
DIRECTOR_EMAIL=director@icmr-nitvar.res.in
EMAIL_HOUSEKEEPING=housekeeping@icmr-nitvar.res.in
EMAIL_IT=it-support@icmr-nitvar.res.in
EMAIL_STATIONERY=stationery@icmr-nitvar.res.in
EMAIL_CANTEEN=canteen@icmr-nitvar.res.in
ACTIVE_MEETING_PROVIDER=mock
```

> 💡 In the NSSM Environment tab, enter each variable on a new line in the format `KEY=VALUE`.

#### I/O tab (optional but recommended for logging):
| Field | Value |
|-------|-------|
| **Output (stdout)** | `D:\HallBooking\logs\app.log` |
| **Error (stderr)** | `D:\HallBooking\logs\error.log` |

Create the logs directory first:
```cmd
mkdir D:\HallBooking\logs
```

#### Click "Install service"

### Start the service

```cmd
nssm start HallBookingSystem
```

### Verify the service is running

```cmd
nssm status HallBookingSystem
```

Should return: `SERVICE_RUNNING`

Or check in **Services** panel: `Win + R` → `services.msc` → find "Hall Booking System".

### Service management commands

```cmd
nssm start HallBookingSystem      # Start
nssm stop HallBookingSystem       # Stop
nssm restart HallBookingSystem    # Restart
nssm status HallBookingSystem     # Check status
nssm remove HallBookingSystem     # Uninstall (with confirmation)
nssm edit HallBookingSystem       # Open GUI to edit settings
```

---

## 12. Step 10 — Test from Another Machine

This is the most important verification step. Do this from a **different computer** on the same LAN.

### Test checklist

| Test | URL | Expected Result |
|------|-----|----------------|
| Booking portal loads | `http://<server-ip>:8000/` | Hall list appears |
| Dashboard loads | `http://<server-ip>:8000/dashboard` | Login screen appears |
| Admin login works | Dashboard → Login | Redirects to dashboard |
| Create a test booking | Portal → fill form → submit | Confirmation + cancel code |
| Check test email | `D:\HallBooking\data\emails.log` | Email logged if SMTP not live |
| Cancel the test booking | Portal → Manage → cancel code → cancel | Status: cancelled |
| Admin sees booking | Dashboard → Live Bookings | Booking visible in list |
| Admin can approve | Dashboard → Pending Approvals | (If approval-required hall used) |
| Audit log records | Dashboard → Audit Log | Actions logged |

---

## 13. Step 11 — Configure SMTP Email

If your institution has an SMTP relay, configure it here. This makes director approval emails, booking confirmations, and department notifications work.

### Option A: Use Institution's SMTP Relay (Recommended)

Ask your mail administrator for:
- SMTP server hostname (e.g., `smtp.icmr-nitvar.res.in`)
- Port (`587` for STARTTLS, `465` for SSL, `25` for plain)
- Authentication credentials (username + password) or whether IP-based relay is allowed
- The "from" address that's permitted to send mail

Then update these settings in **Admin Dashboard → Settings**.

### Option B: Use Gmail SMTP (for testing)

If you don't have an institutional SMTP yet, you can use a Gmail account temporarily:

1. Create a dedicated Gmail account (e.g., `hallbooking.icmrnitvar@gmail.com`)
2. Enable 2-Factor Authentication on the Gmail account
3. Go to Google Account → Security → App Passwords → Create an App Password
4. Use these settings:

| Setting | Value |
|---------|-------|
| `smtp_host` | `smtp.gmail.com` |
| `smtp_port` | `587` |
| `smtp_username` | `hallbooking.icmrnitvar@gmail.com` |
| `smtp_password` | *(the 16-char app password from Google)* |
| `smtp_from` | `hallbooking.icmrnitvar@gmail.com` |
| `smtp_use_tls` | `true` |

### Option C: No SMTP (Fallback Logging)

If SMTP is not yet available, the system **automatically falls back** to logging all emails to:
```
D:\HallBooking\data\emails.log
```

You can manually read this file to see what would have been sent. This is suitable for testing but not for production use.

### Test email delivery

1. In the Admin Dashboard, go to **Email Notifications** tab
2. Click **Send Now** (triggers a test notification)
3. Check the recipient inboxes — or check `data/emails.log` if using file fallback

---

## 14. Step 12 — Seed Your Real Data

Before announcing to staff, replace the sample data with your institution's actual data.

### Replacing sample halls

1. Dashboard → **Hall Management**
2. Set sample halls to inactive (Edit → Active = Off)
3. Add your real halls with accurate names, capacities, and approval flags

### Adding all features

1. Dashboard → **Feature Catalog**
2. Add features for every piece of equipment available across your halls:
   - Audio: Microphone (with type options), PA System, Hearing Loop
   - Visual: Projector, LED Screen, Whiteboard, Interactive Board
   - Connectivity: Video Conference, HDMI, VGA
   - Climate: Air Conditioning, Heater
   - Other: Podium, Stage, Recording Equipment

### Assigning features to halls

For each hall:
1. Dashboard → **Hall Management** → click on a hall
2. In the Features section, assign each piece of equipment the hall has

### Reviewing dropdown options

1. Dashboard → **Dropdown Config**
2. Review and update **Departments** — add any missing divisions
3. Review and update **Designations** — match actual grades in use
4. Review and update **Stationery** — match items stocked by the stationery store

---

## 15. Step 13 — Announce the URL to Staff

Once everything is configured and tested, communicate the system to staff.

### Draft an announcement email

```
Subject: New Online Hall Booking System Now Available

Dear All,

The IT department is pleased to announce the launch of the online Hall Booking System,
available to all staff on the institute network.

📌 Booking Portal: http://192.168.x.x:8000/
   (Works in any browser — Chrome, Firefox, Edge)

How to book a hall:
1. Open the portal link above
2. Select a hall and date
3. Choose your time slot
4. Fill in the booking form
5. Save your Cancel Code — you will need it to manage your booking

Important notes:
- No login required — just enter your name and department
- Some halls require Director's approval
- You will receive email confirmation once the booking is finalized
- Save your Cancel Code to modify or cancel your booking later

For help, contact: it-support@icmr-nitvar.res.in

IT Department, ICMR-NITVAR
```

### Distribute the URL

- Add it to the institute intranet / notice board
- Print and post at common areas (reception, corridors)
- Send to department heads to cascade

---

## 16. Ongoing Maintenance

### Daily check (< 2 minutes)

```cmd
nssm status HallBookingSystem
```
Should show `SERVICE_RUNNING`. If not, restart it:
```cmd
nssm restart HallBookingSystem
```

Also verify the portal loads from a browser.

### Weekly backup

Create a scheduled task or run this manually every week:

```cmd
@echo off
set BACKUP_DIR=D:\HallBooking\backups
set DATE_STR=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
copy "D:\HallBooking\data\hall_booking.db" "%BACKUP_DIR%\hall_booking_%DATE_STR%.db"
echo Backup completed: hall_booking_%DATE_STR%.db
```

Save this as `D:\HallBooking\backup.bat` and create a Windows Scheduled Task to run it weekly.

### Creating the scheduled backup task

```cmd
schtasks /create ^
  /tn "HallBookingBackup" ^
  /tr "D:\HallBooking\backup.bat" ^
  /sc weekly ^
  /d MON ^
  /st 08:00 ^
  /ru SYSTEM
```

### Reviewing logs

Check for issues in:

| Log File | Contains |
|----------|---------|
| `D:\HallBooking\logs\app.log` | Server startup and request logs |
| `D:\HallBooking\logs\error.log` | Python errors |
| `D:\HallBooking\data\emails.log` | Email fallback log |

### Updating the application

When a new version of the code is available:

```cmd
nssm stop HallBookingSystem

REM Backup first!
copy D:\HallBooking\data\hall_booking.db D:\HallBooking\data\hall_booking_before_update.db

REM Copy new files (do NOT delete the data\ folder)
REM ... copy new app\, static\ folders here ...

REM Update dependencies if requirements.txt changed
D:\HallBooking\.venv\Scripts\activate
pip install -r D:\HallBooking\requirements.txt

nssm start HallBookingSystem
```

---

## 17. Uninstall / Teardown

If you need to remove the application:

```cmd
REM Stop and remove the service
nssm stop HallBookingSystem
nssm remove HallBookingSystem confirm

REM Remove the firewall rule
netsh advfirewall firewall delete rule name="Hall Booking System"

REM Delete the application folder
rmdir /s /q D:\HallBooking
```

---

## 18. Quick Troubleshooting Reference

### Server won't start

```cmd
REM Check if port is already in use
netstat -ano | findstr :8000

REM Kill the process using port 8000 (replace XXXX with PID)
taskkill /PID XXXX /F

REM Try starting again
cd D:\HallBooking
.venv\Scripts\activate
set_env.bat
python run.py
```

### Portal not accessible from other machines

```cmd
REM Check firewall rule exists
netsh advfirewall firewall show rule name="Hall Booking System"

REM Re-add if missing
netsh advfirewall firewall add rule name="Hall Booking System" dir=in action=allow protocol=TCP localport=8000

REM Verify server is listening on 0.0.0.0 (not just localhost)
netstat -an | findstr :8000
REM Should show: 0.0.0.0:8000  LISTENING
```

### Dashboard login not working

```cmd
REM Check the admin user exists in the database
cd D:\HallBooking
.venv\Scripts\python.exe -c "
from app.database import SessionLocal
from app.models import User
db = SessionLocal()
users = db.query(User).all()
for u in users: print(u.username, u.role)
db.close()
"
```

If no users exist, delete the database and restart to re-seed:
```cmd
del data\hall_booking.db
python run.py
```

### Emails not being sent

```cmd
REM Check emails.log to see if fallback is being used
type D:\HallBooking\data\emails.log

REM Test SMTP connectivity manually
python -c "
import smtplib
try:
    s = smtplib.SMTP('smtp.icmr-nitvar.res.in', 587, timeout=5)
    print('Connected OK')
    s.starttls()
    s.login('user', 'pass')
    print('Login OK')
    s.quit()
except Exception as e:
    print('Error:', e)
"
```

### Service not starting after reboot

```cmd
REM Check service status and error
nssm status HallBookingSystem
sc query HallBookingSystem

REM View Windows Event Log for service errors
eventvwr
REM → Windows Logs → Application → filter by "HallBookingSystem"

REM Check if Python path is correct
D:\HallBooking\.venv\Scripts\python.exe --version
```

### Database corruption / errors

```cmd
REM Check database integrity
sqlite3 D:\HallBooking\data\hall_booking.db "PRAGMA integrity_check;"
REM Should return: ok

REM Restore from backup if corrupted
copy D:\HallBooking\backups\hall_booking_YYYYMMDD.db D:\HallBooking\data\hall_booking.db
```

> 💡 **Install sqlite3 CLI:** Download from https://www.sqlite.org/download.html — get `sqlite-tools-win-x64-*.zip`, extract `sqlite3.exe` to `D:\HallBooking\` or anywhere in your PATH.

---

## Summary: Minimum Viable Production Setup

Here's the condensed checklist for a production-ready deployment:

```
☐ Python 3.10+ installed
☐ Project files at D:\HallBooking\
☐ Virtual environment created (.venv\)
☐ Dependencies installed (pip install -r requirements.txt)
☐ set_env.bat created with real values
☐ HALL_SECRET set to a long random string
☐ HALL_ADMIN_PASS set to a strong password (NOT "admin")
☐ SMTP settings configured
☐ First run tested — portal and dashboard both load
☐ Admin password changed in dashboard
☐ base_url set to http://<server-actual-ip>:8000
☐ Department emails set to real addresses
☐ Real halls added and sample halls archived
☐ Hall features configured
☐ Dropdown options updated to match institute
☐ Firewall port 8000 opened
☐ NSSM service installed and set to Automatic start
☐ Service tested across a LAN reboot
☐ Tested from a different machine on the LAN
☐ Email delivery tested
☐ Weekly backup task created
☐ URL announced to staff
```

---

*Document maintained by IT Department, ICMR-NITVAR*
*For issues, see [DOCUMENTATION.md](DOCUMENTATION.md) or the [SOP.md](SOP.md)*

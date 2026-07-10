# Standard Operating Procedures (SOP)
## ICMR-NITVAR Hall Booking System

> **Document No:** SOP-HBS-001 | **Version:** 1.0 | **Effective Date:** July 2026
> **Prepared by:** IT Department, ICMR-NITVAR | **Approved by:** Director's Office

---

## Table of Contents

**Part A — For Bookers (General Staff)**
- [SOP-01: How to Book a Hall](#sop-01-how-to-book-a-hall)
- [SOP-02: How to View or Manage an Existing Booking](#sop-02-how-to-view-or-manage-an-existing-booking)
- [SOP-03: How to Cancel a Booking](#sop-03-how-to-cancel-a-booking)
- [SOP-04: Requesting a Virtual Meeting Link](#sop-04-requesting-a-virtual-meeting-link)
- [SOP-05: Director Approval — What to Expect](#sop-05-director-approval--what-to-expect)

**Part B — For the Director's Office**
- [SOP-06: Approving or Rejecting a Booking Request](#sop-06-approving-or-rejecting-a-booking-request)

**Part C — For IT Administrators**
- [SOP-07: Logging into the Admin Dashboard](#sop-07-logging-into-the-admin-dashboard)
- [SOP-08: Managing Halls (Create / Edit / Archive)](#sop-08-managing-halls-create--edit--archive)
- [SOP-09: Managing the Feature Catalog & Hall Equipment](#sop-09-managing-the-feature-catalog--hall-equipment)
- [SOP-10: Managing Dropdown Options](#sop-10-managing-dropdown-options)
- [SOP-11: Approving or Rejecting Bookings from the Dashboard](#sop-11-approving-or-rejecting-bookings-from-the-dashboard)
- [SOP-12: Configuring Email Settings](#sop-12-configuring-email-settings)
- [SOP-13: Manually Triggering Department Notifications](#sop-13-manually-triggering-department-notifications)
- [SOP-14: Viewing the Audit Log](#sop-14-viewing-the-audit-log)
- [SOP-15: Changing Admin Credentials](#sop-15-changing-admin-credentials)
- [SOP-16: First-Time Server Setup](#sop-16-first-time-server-setup)
- [SOP-17: Routine Server Maintenance & Backup](#sop-17-routine-server-maintenance--backup)
- [SOP-18: Troubleshooting Common Issues](#sop-18-troubleshooting-common-issues)

---

# PART A — FOR BOOKERS (GENERAL STAFF)

---

## SOP-01: How to Book a Hall

**Who:** Any ICMR-NITVAR staff member  
**When:** Whenever a conference hall or meeting room is needed  
**Prerequisites:** Access to the LAN / institute network

### Steps

1. **Open the Booking Portal**
   - Open a web browser and go to: `http://<server-ip>:8000/`
   - *(The IT department will provide you with the exact server address.)*

2. **Browse Available Halls**
   - You will see a list of available halls with their name, capacity, and features.
   - Use the **capacity filter** (if shown) to find a hall that fits your group size.
   - Click on a hall card to proceed.

3. **Select a Date**
   - Use the date picker to choose the date you need the hall.
   - Click **Check Availability**.

4. **Choose a Time Slot**
   - The time grid displays all existing bookings for that date as coloured blocks.
   - Click on a free (white/light) slot to select your **start time**.
   - Then click on another slot to set your **end time** (or drag if supported).
   - Available hours are 09:00 – 18:00.

5. **Fill in the Booking Form**
   - Complete all required fields:

   | Field | Required? | Notes |
   |-------|-----------|-------|
   | **Your Name** | Yes | Full name of the requester |
   | **Department** | Yes | Select from dropdown |
   | **Scientist Designation** | Recommended | Select from dropdown |
   | **Purpose of Meeting** | Yes | Brief description |
   | **Expected Attendees** | Yes | Number of people |
   | **Project ID** | If applicable | Grant/project reference code |
   | **Coordinator Name** | Yes | Person managing on-ground |
   | **Coordinator Phone** | Yes | Contact during the meeting |
   | **Coordinator Email** | Yes | Confirmation email is sent here |

   - **Optional services** (select as needed):
     - IT Support Staff — Request AV/tech assistance
     - Housekeeping — Request room setup/cleanup
     - Virtual Meeting Link — Auto-generate a Zoom/Meet link
     - Stationery — List items (e.g., "Notebooks x5, Pens x10")
     - Catering / Refreshments — Describe needs (e.g., "Tea for 15")
     - Equipment/Features — Describe AV or special equipment needed

6. **Submit the Booking**
   - Click **Book Now** (or **Submit Booking**).
   - If the slot is still free, you will see a **Booking Confirmation** screen.

7. **Save Your Cancel Code**
   - A unique **6-character Cancel Code** (e.g., `XK7MQP`) will be shown.
   - **Write this down or take a screenshot.** This is the only way to manage your booking later.
   - A confirmation email will also be sent to your coordinator's email address (if provided).

> ⚠️ **Important:** If the hall you selected requires **Director's Approval**, your booking will show as *Pending Approval* rather than *Confirmed*. You will receive an email once the Director decides. See SOP-05.

---

## SOP-02: How to View or Manage an Existing Booking

**Who:** Bookers who hold a cancel code  
**Prerequisites:** Your 6-character cancel code

### Steps

1. Go to `http://<server-ip>:8000/`
2. Click **Manage Booking** (or equivalent link on the portal).
3. Enter your **Cancel Code** and click **Find Booking**.
4. Your booking details will be displayed, including:
   - Hall, date, time, status
   - Coordinator details
   - Cancel code
   - Virtual meeting link (if generated)
5. You may:
   - **View** the full booking receipt.
   - **Edit** the booking (date, time, details) — subject to availability.
   - **Cancel** the booking (see SOP-03).

---

## SOP-03: How to Cancel a Booking

**Who:** Bookers (self-cancellation)  
**Prerequisites:** Your 6-character cancel code

### Steps

1. Navigate to **Manage Booking** on the portal.
2. Enter your **Cancel Code** and click **Find Booking**.
3. Click **Cancel Booking**.
4. Confirm the cancellation when prompted.
5. The booking status changes to **Cancelled**.

> ℹ️ Once cancelled, the time slot becomes available for others to book immediately.

> ℹ️ If you have lost your cancel code, contact the IT department with your name, department, hall name, and date — they can cancel it from the admin dashboard.

---

## SOP-04: Requesting a Virtual Meeting Link

**Who:** Bookers who need a virtual attendance option  
**When:** During the booking creation step

### Steps

1. In the booking form (Step 5 of SOP-01), check the box:
   **"Request Virtual Meeting Link (Zoom / Google Meet)"**
2. Complete and submit the booking.
3. If the booking is **immediately confirmed** (no approval required):
   - A virtual meeting link is generated automatically.
   - The link appears on your booking receipt and in the confirmation email.
4. If the booking is **pending Director's approval**:
   - The meeting link will be generated only after the Director approves.
   - It will be included in the confirmation email sent after approval.

> ℹ️ The meeting link provider (Zoom, Google Meet, or Mock) is configured by the IT department. Contact IT if you need a specific platform.

---

## SOP-05: Director Approval — What to Expect

**Who:** Staff booking halls that require Director approval  
**Which halls:** Halls marked as "Requires Approval" (visible on the hall card)

### What Happens

| Step | What Occurs |
|------|------------|
| You submit the booking | Status shows **Pending Approval** |
| System emails Director | Automated email with booking details + Approve/Reject buttons |
| Director acts | Clicks Approve or Reject in the email |
| You are notified | Confirmation or rejection email sent to coordinator's email |

### Expected Timeline

- The Director is notified **immediately** upon booking submission.
- Approval decisions typically come within the same business day.
- If no response is received within 24 hours, contact the Director's Office directly.

### If Approved

- Your booking becomes **Confirmed**.
- A confirmation email is sent to the coordinator's email with:
  - Hall, date, time
  - Your cancel code
  - Virtual meeting link (if requested)

### If Rejected

- Your booking is **Cancelled**.
- A rejection notice is sent to the coordinator's email.
- You are free to book a different hall or time slot.

---

# PART B — FOR THE DIRECTOR'S OFFICE

---

## SOP-06: Approving or Rejecting a Booking Request

**Who:** Director or authorized Director's Office staff  
**Prerequisites:** Email access

### Steps

1. **Receive the Approval Request Email**
   - Subject: `📋 Director Approval Required: <Hall Name> - <Date>`
   - The email contains full booking details:
     - Date, time, hall
     - Requester name, designation, department
     - Coordinator contact
     - Purpose and expected attendees

2. **Review the Request**
   - Read the booking details carefully.
   - Ensure there are no conflicts with institutional requirements.

3. **Click Approve or Reject**

   | Button | Action |
   |--------|--------|
   | **Approve Booking** (green) | Opens a confirmation page. Click "Yes, Approve" to confirm. |
   | **Reject Booking** (red) | Opens a confirmation page. Click "Yes, Decline" to confirm. |

4. **Confirmation Page**
   - Before any action is taken, you will see a summary confirmation page.
   - Click the appropriate button to finalize.

5. **Outcome**
   - **Approved:** Booking moves to Confirmed; coordinator receives confirmation email.
   - **Rejected:** Booking is cancelled; coordinator receives rejection email.

> ℹ️ The approve/reject links work only once. If the booking has already been processed (or cancelled by the booker), the page will show a notice.

> ⚠️ **No login is required** — the secure link in the email is sufficient authentication for this action.

---

# PART C — FOR IT ADMINISTRATORS

---

## SOP-07: Logging into the Admin Dashboard

**Who:** IT administrators  
**URL:** `http://<server-ip>:8000/dashboard`

### Steps

1. Navigate to `http://<server-ip>:8000/dashboard`.
2. Enter your **username** and **password**.
3. Click **Login**.
4. You will be taken to the main dashboard view.

> ℹ️ Default credentials: `admin` / `admin`. **Change these immediately on first use** (see SOP-15).

### Logging Out

- Click **Logout** (top-right corner of the dashboard).
- Session cookie is cleared; you must log in again to access the dashboard.

---

## SOP-08: Managing Halls (Create / Edit / Archive)

**Who:** IT administrators

### Creating a New Hall

1. In the dashboard, go to the **Hall Management** tab.
2. Click **+ Add Hall**.
3. Fill in:
   - **Hall Name** — e.g., "Conference Hall A"
   - **Capacity** — Maximum number of occupants
   - **Requires Director Approval** — Check if this is a premium/restricted hall
4. Click **Save**.
5. Optionally, upload a **hall image** by clicking the image area or upload button.

### Editing a Hall

1. Find the hall in the Hall Management tab.
2. Click **Edit** (pencil icon).
3. Update any fields (name, capacity, approval flag).
4. Click **Save**.

> ℹ️ Renaming a hall is safe — bookings reference the internal hall ID, not the name.

### Uploading a Hall Image

1. Click on the hall or its edit button.
2. Click **Upload Image** / **Change Photo**.
3. Select a `.jpg`, `.jpeg`, `.png`, `.webp`, or `.gif` file.
4. The image is saved to `static/images/hall_<id>.<ext>` and displayed in the portal.

### Archiving (Soft-Deleting) a Hall

1. Click **Edit** on the hall.
2. Toggle **Active** to **Off** (or click **Archive**).
3. Click **Save**.

> ℹ️ Archived halls no longer appear in the public booking portal. All historical bookings for that hall are preserved in the database.

### Restoring an Archived Hall

1. Find the hall in the list (it may show as "Inactive").
2. Edit it and toggle **Active** back to **On**.

---

## SOP-09: Managing the Feature Catalog & Hall Equipment

Features describe what equipment is available in each hall (e.g., Microphone, Projector, Whiteboard).

### Creating a Feature Type

1. Go to **Feature Catalog** tab.
2. Click **+ Add Feature**.
3. Enter:
   - **Feature Name** — e.g., "Microphone"
   - **Value Type**:
     - `bool` — simple Yes/No
     - `number` — numeric count
     - `text` — free-text description
     - `single_select` — one choice from a list
     - `multi_select` — multiple choices from a list
4. Click **Save**.

### Adding Options to a Select Feature

*(Only for `single_select` or `multi_select` features)*

1. Find the feature in the catalog.
2. Click **+ Add Option**.
3. Enter the option label (e.g., "Handheld Wireless", "Lavalier").
4. Optionally set a sort order.
5. Click **Save**.

### Assigning Features to a Hall

1. In **Hall Management**, click on a hall.
2. Go to its **Features** section.
3. Select a **Feature** from the dropdown.
4. Select an **Option** (for select-type features).
5. Enter **Quantity** if applicable (e.g., 2 for two microphones).
6. Click **Assign**.

### Removing a Feature Assignment

1. In the hall's Features section, click **Remove** next to the unwanted assignment.

### Retiring a Feature or Option

- Click **Edit** on a feature/option.
- Toggle **Active** to **Off**.
- Retired features/options are hidden from the portal but retained in the database.

---

## SOP-10: Managing Dropdown Options

Dropdown options control what appears in the **Department**, **Designation**, and **Stationery** dropdown menus on the public booking portal.

### Adding a Dropdown Option

1. Go to **Dropdown Config** tab.
2. Select the **Category**: `department`, `designation`, or `stationery`.
3. Enter the **Value** (e.g., "Administration", "Scientist-B", "Ballpoint Pens").
4. Click **Add**.

### Removing a Dropdown Option

1. Find the option in the list.
2. Click **Delete** (trash icon).
3. Confirm deletion.

> ⚠️ Removing a dropdown option does not affect existing bookings that used that value. It only removes it from future booking forms.

---

## SOP-11: Approving or Rejecting Bookings from the Dashboard

In addition to the director's email flow, IT admins can approve/reject pending bookings directly.

### Steps

1. Go to the **Pending Approvals** tab (or filter the Bookings tab by `status=pending_approval`).
2. Find the booking to act on.
3. Click:
   - **Approve** (✓) — Booking confirmed; coordinator notified.
   - **Reject** (✗) — Booking cancelled; coordinator notified.
4. The booking status updates immediately.

---

## SOP-12: Configuring Email Settings

Email settings can be updated at runtime from the dashboard without restarting the server.

### Updating SMTP Settings

1. Go to **Settings** tab (or **Email Notifications** section).
2. Update the following fields as needed:

   | Setting | Description |
   |---------|-------------|
   | SMTP Host | Your mail server address |
   | SMTP Port | Port number (e.g., 587 for TLS) |
   | SMTP Username | Authentication username |
   | SMTP Password | Authentication password |
   | From Address | Sender email shown to recipients |
   | Use TLS | Enable STARTTLS (recommended for port 587) |

3. Click **Save Settings**.

### Updating Department Email Addresses

1. In the **Settings** tab, update:

   | Key | Description |
   |-----|-------------|
   | `email_housekeeping` | Housekeeping team email |
   | `email_it` | IT support team email |
   | `email_stationery` | Stationery store email |
   | `email_canteen` | Canteen / catering team email |
   | `director_email` | Director's Office email for approvals |

2. Click **Save Settings**.

### Updating Email Templates

1. In the **Settings** tab, find the template fields:
   - `template_housekeeping`
   - `template_it`
   - `template_stationery`
   - `template_canteen`
2. Modify the HTML template as needed. Use `{date}` for tomorrow's date and `{table}` for the meetings table.
3. Click **Save Settings**.

### Setting the Base URL

The `base_url` setting is used in director approval email links.

1. In the **Settings** tab, find `base_url`.
2. Set it to the server's accessible address, e.g., `http://192.168.1.10:8000`
3. Click **Save Settings**.

> ℹ️ The base URL must be reachable by the Director when they open the email.

---

## SOP-13: Manually Triggering Department Notifications

The daily notification normally fires automatically at 18:00. However, you can trigger it manually if needed.

### Steps

1. Go to **Email Notifications** tab in the dashboard.
2. Click **Send Now** (or **Trigger Notifications**).
3. The system queries tomorrow's bookings and dispatches emails immediately.
4. A success or error message will be displayed.

> ⚠️ This does not update the `last_summary_notification_date` guard. If triggered manually before 18:00, the automatic scheduler will still fire at 18:00.

---

## SOP-14: Viewing the Audit Log

The audit log provides a read-only record of all significant actions.

### Steps

1. Go to the **Audit Log** tab.
2. The log shows (newest first):
   - **Timestamp** (UTC)
   - **Action** (e.g., `booking.create`, `hall.update`)
   - **Entity & ID** (e.g., `booking #42`)
   - **Actor** (admin username or booker name)
   - **IP Address**
   - **Detail** (change summary)
3. Up to 500 entries can be loaded.

### Common Audit Actions

| Action | Meaning |
|--------|---------|
| `booking.create` | New booking submitted |
| `booking.cancel` | Booking cancelled by booker |
| `booking.update` | Booking modified by booker |
| `booking.approve` | Admin approved a pending booking |
| `booking.reject` | Admin rejected a pending booking |
| `hall.create` | New hall created |
| `hall.update` | Hall settings changed |
| `settings.update` | System settings modified |

---

## SOP-15: Changing Admin Credentials

**Do this immediately after the first server deployment.**

### Steps

1. Log into the dashboard.
2. Go to **Account Settings** tab.
3. Enter:
   - **New Username**
   - **New Password** (minimum 8 characters recommended)
4. Click **Save Credentials**.
5. You will be automatically logged in with the new credentials.

> ⚠️ Do not use the default `admin/admin` credentials in a production environment. Anyone with LAN access can reach the dashboard URL.

---

## SOP-16: First-Time Server Setup

**Who:** IT administrator deploying the system for the first time

### Pre-Deployment Checklist

- [ ] Python 3.10+ installed on the server
- [ ] Server is on the institution LAN
- [ ] SMTP relay or mail server credentials available
- [ ] Institution IP range / firewall allows port 8000

### Deployment Steps

```powershell
# Step 1: Navigate to project directory
cd D:\Work\Projects\hall-booking

# Step 2: Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Set environment variables
$env:HALL_SECRET = "Generate-A-Long-Random-String-Here"
$env:HALL_ADMIN_USER = "admin"
$env:HALL_ADMIN_PASS = "ChangeThisImmediately123"
$env:SMTP_HOST = "smtp.icmr-nitvar.res.in"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "noreply@icmr-nitvar.res.in"
$env:SMTP_PASSWORD = "your-smtp-password"
$env:SMTP_USE_TLS = "true"
$env:DIRECTOR_EMAIL = "director@icmr-nitvar.res.in"
$env:EMAIL_HOUSEKEEPING = "housekeeping@icmr-nitvar.res.in"
$env:EMAIL_IT = "it-support@icmr-nitvar.res.in"
$env:EMAIL_STATIONERY = "stationery@icmr-nitvar.res.in"
$env:EMAIL_CANTEEN = "canteen@icmr-nitvar.res.in"

# Step 5: Start the server
python run.py
```

### Post-Deployment Checklist

- [ ] Open `http://localhost:8000/` — booking portal loads correctly
- [ ] Open `http://localhost:8000/dashboard` — dashboard loads
- [ ] Log in with initial credentials
- [ ] **Change admin password** (SOP-15)
- [ ] Set `base_url` in System Settings to `http://<server-ip>:8000`
- [ ] Add initial halls (SOP-08)
- [ ] Add initial features (SOP-09)
- [ ] Configure department/designation dropdowns (SOP-10)
- [ ] Test a sample booking from a browser on another LAN device
- [ ] Verify confirmation email arrives (check `data/emails.log` if SMTP not configured)
- [ ] Set up Windows Service for persistence (see Deployment Guide)

---

## SOP-17: Routine Server Maintenance & Backup

### Daily

- [ ] Verify server is running (`http://<server-ip>:8000/` returns the portal)
- [ ] Check `data/emails.log` — if emails are logging there instead of being sent, SMTP may be down

### Weekly

- [ ] Back up the database:
  ```powershell
  copy "D:\Work\Projects\hall-booking\data\hall_booking.db" `
       "D:\Backups\hall_booking_$(Get-Date -Format 'yyyyMMdd').db"
  ```
- [ ] Review the audit log for unexpected admin actions

### Monthly

- [ ] Review and update department email addresses in System Settings
- [ ] Archive or delete old backup files
- [ ] Check if `requirements.txt` dependencies need security updates:
  ```powershell
  pip list --outdated
  ```

### Updating the Application

1. Stop the service (`nssm stop HallBooking`)
2. Back up the database
3. Pull / copy new code
4. Activate the virtual environment
5. Run `pip install -r requirements.txt`
6. Restart the service (`nssm start HallBooking`)

---

## SOP-18: Troubleshooting Common Issues

### Issue 1: Portal is not loading

| Check | Action |
|-------|--------|
| Is the server running? | Run `python run.py` or check the Windows Service |
| Is port 8000 blocked? | Allow port 8000 in Windows Firewall |
| Is the URL correct? | Use `http://<server-ip>:8000/` not `https://` |

### Issue 2: Emails are not being received

| Check | Action |
|-------|--------|
| SMTP configured? | Go to Settings tab; verify SMTP host, port, credentials |
| Fallback log | Check `data/emails.log` — emails are logged here when SMTP fails |
| Base URL correct? | In Settings, ensure `base_url` is set to the actual server IP |
| Firewall blocking SMTP? | Verify outbound connection on the configured SMTP port |

### Issue 3: Booking shows "Time slot already taken" but the grid looks free

- This can happen if a booking was just made by someone else while you were filling the form.
- Refresh the hall availability page and try again.
- The system prevents double-bookings via atomic database transactions.

### Issue 4: Director approval email links are not working

| Check | Action |
|-------|--------|
| `base_url` correct? | Set it to the server's LAN IP in System Settings |
| Token expired? | Tokens do not expire — but if booking is already processed, the page will show a notice |
| Server running? | The server must be running when the Director clicks the link |

### Issue 5: Admin dashboard says "Unauthorized" / kicks to login

- Session cookies expire after inactivity.
- Log in again.
- If it happens persistently, the server may have been restarted (sessions are in-memory).

### Issue 6: Virtual meeting links show `https://meet.mock.com/...`

- The system is using the `Mock` provider.
- To use real Zoom/Google Meet links, the IT team must configure API credentials and set `ACTIVE_MEETING_PROVIDER=zoom` or `ACTIVE_MEETING_PROVIDER=google`.
- Contact the development team for provider-specific API integration.

### Issue 7: 15-minute reminders were not sent

- Reminders are tracked in-memory. If the server was restarted within 15 minutes of a meeting start, the reminder state was lost.
- This is a known limitation. The workaround is to ensure the server is running continuously.

### Issue 8: Hall not appearing in the booking portal

- Check if the hall is set to **Active** in the dashboard.
- Archived halls do not appear to bookers.

### Issue 9: Old/unused options in dropdowns

- Remove unused dropdown options from the **Dropdown Config** tab in the admin dashboard.

---

## Quick Reference Cards

### For Bookers

```
Portal URL:    http://<server-ip>:8000/
To book:       Select Hall → Pick Date → Pick Time → Fill Form → Submit
Cancel code:   Save it! It's the only way to manage your booking.
To manage:     Go to portal → Manage Booking → Enter Cancel Code
Need IT help:  Contact the IT department with your booking details
```

### For the Director's Office

```
Approval email subject:  "📋 Director Approval Required: <Hall> - <Date>"
To approve:   Click green "Approve Booking" button in the email
To reject:    Click red "Reject Booking" button in the email
Confirmation: A second page asks you to confirm before the action is taken
No login needed — the email link is your secure authentication
```

### For IT Administrators

```
Dashboard URL:  http://<server-ip>:8000/dashboard
Default login:  admin / admin  (CHANGE IMMEDIATELY)
Database file:  data/hall_booking.db
Email fallback: data/emails.log
Config file:    app/config.py (or set environment variables)
Start server:   python run.py  (or via NSSM Windows Service)
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | July 2026 | IT Department, ICMR-NITVAR | Initial release |

---

*For questions or issues not covered in this SOP, contact the IT Department.*

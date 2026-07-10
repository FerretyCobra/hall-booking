# Project Tasks & TODOs

Here is a list of features and enhancements implemented in the Hall Booking system.

## Pending Features

### 📅 End-of-Day Department Notifications
**Description:**
Automatically send an email at the end of each day to key departments (Housekeeping, IT Staff, Stationery Store, and Canteen) summarizing tomorrow's schedule of meetings and their respective resource requirements.

**Tasks:**
- [x] Set up database query to fetch tomorrow's bookings dynamically (`booking_date == today + 1`).
- [x] Define recipient emails for each department (Housekeeping, IT, Stationery, Canteen).
- [x] Format email body with:
  - Hall name & meeting timings
  - Expected attendee count (for Canteen & Housekeeping)
  - IT support flag & requested features (for IT Staff & Stationery)
  - Coordinator name & contact phone number (so teams know who to contact)
- [x] Configure SMTP/Email client integration (`app/config.py`).
- [x] Implement the scheduler (either using `APScheduler` inside the application or via an OS cron job calling a custom CLI command/script).

### 🔑 Director Approval for Specific Halls
**Description:**
Certain premium halls require explicit acceptance/approval from the Director's Office. When someone requests a booking for one of these halls, an email notification must be sent to the Director's Office to request approval.

**Tasks:**
- [x] Add a flag (e.g., `requires_approval` boolean) to the `Hall` model.
- [x] Implement booking approval workflow:
  - Bookings for these halls start in a `pending_approval` status rather than `confirmed`.
  - Send an automated email containing the booking details and quick approval/rejection links to the Director's Office.
- [x] Create endpoint/interface for the Director's Office to approve or reject pending bookings.
- [x] Send confirmation or rejection email back to the booker once decided.

### 🛠️ General Booking & Dashboard Enhancements
**Description:**
Additional changes to capture contact information, display crucial booking details on receipts, and allow admins/IT staff to configure drop-down choices dynamically.

**Tasks:**
- [x] **Coordinator Details:**
  - Add `coordinator_name` and `coordinator_phone` columns to the `Booking` model.
  - Add fields for coordinator name and phone number to the booking creation form.
- [x] **Booking Receipt:**
  - Include the `attendees_count` (number of attendees) in the final booking receipt screen/PDF.
- [x] **Configurable Dropdowns:**
  - Make personal details drop-down lists (e.g., departments, designations, projects) configurable dynamically in the admin/IT dashboard rather than hardcoded.

### 🎥 Automated Virtual Meeting Integration (Modular)
**Description:**
Automatically generate Zoom or Google Meet links for bookings that request a virtual meeting. To accommodate not having a paid developer account yet, this must be built as a modular service that can easily switch between Zoom, Google Meet, or a Mock/Manual link generator via environment variables.

**Tasks:**
- [x] **Database & UI Fields:**
  - Add `virtual_meeting_requested` (boolean) and `meeting_link` (string) to the `Booking` model.
  - Add a "Request Zoom/Google Meet Link" option in the booking request form.
- [x] **Modular Meeting Service Interface:**
  - Design a generic `MeetingProvider` interface with a `create_meeting(booking_details)` method.
  - Create three providers:
    1. `MockMeetingProvider`: Generates dummy links (useful for local development/testing without API keys).
    2. `ZoomMeetingProvider`: Integrates with Zoom Server-to-Server OAuth API.
    3. `GoogleMeetProvider`: Integrates with Google Workspace Calendar API.
  - Configure the active provider and API credentials dynamically via env variables in `app/config.py` (e.g., `ACTIVE_MEETING_PROVIDER = "mock" | "zoom" | "google"`).
- [x] **Integration & Notifications:**
  - Call the active meeting service when a booking is confirmed.
  - Save the generated link back to the booking record.
  - Include the generated link in the confirmation emails and the booking receipt.




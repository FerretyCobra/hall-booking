from datetime import date, timedelta
from sqlalchemy.orm import Session
from ..models import Booking, Hall
from ..config import DEPARTMENT_EMAILS
from .email import send_email
from .settings import get_setting


# ---------------------------------------------------------------------------
# Shared HTML primitives
# ---------------------------------------------------------------------------

_BRAND_COLOR   = "#1a56db"
_BRAND_DARK    = "#1e3a6e"
_SUCCESS_COLOR = "#16a34a"
_DANGER_COLOR  = "#dc2626"
_WARN_COLOR    = "#d97706"
_TEXT_DARK     = "#1f2937"
_TEXT_MID      = "#374151"
_TEXT_LIGHT    = "#6b7280"
_BG_LIGHT      = "#f3f6fb"
_BORDER        = "#e5e7eb"


def _base_layout(preheader: str, body_html: str) -> str:
    """Responsive email shell with ICMR-NITVAR branded gradient header."""
    return (
        "<!DOCTYPE html>"
        "<html lang='en'>"
        "<head>"
        "<meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
        "<title>ICMR-NITVAR Hall Booking</title>"
        "</head>"
        f"<body style='margin:0;padding:0;background-color:{_BG_LIGHT};"
        f"font-family:Segoe UI,Arial,sans-serif;color:{_TEXT_DARK};'>"
        f"<span style='display:none;max-height:0;overflow:hidden;'>{preheader}</span>"
        f"<table width='100%' cellpadding='0' cellspacing='0' border='0'"
        f" style='background-color:{_BG_LIGHT};padding:30px 0;'>"
        "<tr><td align='center'>"
        "<table width='620' cellpadding='0' cellspacing='0' border='0'"
        f" style='background-color:#ffffff;border-radius:8px;"
        f"box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;'>"
        # Header
        f"<tr><td style='background:linear-gradient(135deg,{_BRAND_DARK} 0%,{_BRAND_COLOR} 100%);"
        f"padding:28px 36px;'>"
        "<div style='color:#ffffff;font-size:20px;font-weight:700;letter-spacing:.5px;line-height:1.2;'>"
        "ICMR &ndash; National Institute for Traditional Varmam Sciences"
        "</div>"
        "<div style='color:rgba(255,255,255,.75);font-size:13px;margin-top:4px;'>"
        "Hall Booking Management System"
        "</div>"
        "</td></tr>"
        # Body
        f"<tr><td style='padding:32px 36px;'>{body_html}</td></tr>"
        # Footer
        f"<tr><td style='background-color:#f9fafb;border-top:1px solid {_BORDER};"
        f"padding:20px 36px;'>"
        f"<p style='margin:0;font-size:12px;color:{_TEXT_LIGHT};line-height:1.6;'>"
        "This is an automated message from the "
        "<strong>Hall Booking Management System</strong> at ICMR-NITVAR. "
        "Please do not reply directly to this email. "
        "For assistance, contact your system administrator."
        "</p></td></tr>"
        "</table></td></tr></table>"
        "</body></html>"
    )


def _section_heading(title: str, icon: str = "") -> str:
    prefix = f"{icon} " if icon else ""
    return (
        f"<h2 style='margin:0 0 8px;font-size:22px;font-weight:700;color:{_BRAND_DARK};'>"
        f"{prefix}{title}</h2>"
    )


def _divider() -> str:
    return f"<hr style='border:none;border-top:1px solid {_BORDER};margin:20px 0;'/>"


def _detail_row(label: str, value: str, highlight: bool = False) -> str:
    bg = "#eff6ff" if highlight else "#ffffff"
    return (
        "<tr>"
        f"<td style='padding:10px 14px;border:1px solid {_BORDER};width:38%;"
        f"background-color:#f9fafb;font-weight:600;color:{_TEXT_MID};"
        f"font-size:14px;vertical-align:top;'>{label}</td>"
        f"<td style='padding:10px 14px;border:1px solid {_BORDER};"
        f"background-color:{bg};color:{_TEXT_DARK};font-size:14px;'>{value}</td>"
        "</tr>"
    )


def _detail_table(*rows_html: str) -> str:
    inner = "".join(rows_html)
    return (
        "<table cellpadding='0' cellspacing='0' border='0' "
        f"style='width:100%;border-collapse:collapse;margin-top:16px;'>"
        f"{inner}</table>"
    )


def _cta_button(label: str, url: str, color: str) -> str:
    return (
        f"<a href='{url}' style='display:inline-block;padding:12px 28px;"
        f"background-color:{color};color:#ffffff;text-decoration:none;"
        f"border-radius:6px;font-size:15px;font-weight:600;"
        f"letter-spacing:.3px;line-height:1;'>{label}</a>"
    )


def _info_box(message: str, color: str = _BRAND_COLOR) -> str:
    return (
        f"<div style='background-color:{color}18;border-left:4px solid {color};"
        f"padding:14px 18px;border-radius:0 6px 6px 0;"
        f"color:{_TEXT_MID};font-size:14px;line-height:1.6;'>{message}</div>"
    )


def format_meeting_rows(meetings: list, cols: list) -> str:
    """Render meetings as a styled, striped HTML table."""
    if not meetings:
        return _info_box("No meetings are currently scheduled.", color=_TEXT_LIGHT)

    header_cells = "".join(
        f"<th style='padding:10px 12px;text-align:left;"
        f"background-color:{_BRAND_DARK};color:#ffffff;"
        f"font-size:13px;font-weight:600;white-space:nowrap;'>{col}</th>"
        for col in cols
    )

    rows_html = ""
    for i, m in enumerate(meetings):
        bg = "#f9fafb" if i % 2 == 0 else "#ffffff"
        cells = "".join(
            f"<td style='padding:10px 12px;border-bottom:1px solid {_BORDER};"
            f"background-color:{bg};font-size:13px;color:{_TEXT_DARK};"
            f"vertical-align:top;'>{m.get(col, '')}</td>"
            for col in cols
        )
        rows_html += f"<tr>{cells}</tr>"

    return (
        "<div style='overflow-x:auto;'>"
        "<table cellpadding='0' cellspacing='0' border='0' "
        f"style='width:100%;border-collapse:collapse;border-radius:6px;"
        f"overflow:hidden;border:1px solid {_BORDER};margin-top:12px;'>"
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{rows_html}</tbody></table></div>"
    )

def send_department_notifications(db: Session):
    tomorrow = date.today() + timedelta(days=1)

    # Query tomorrow's confirmed bookings
    bookings = (
        db.query(Booking, Hall)
        .join(Hall, Booking.hall_id == Hall.id)
        .filter(Booking.booking_date == tomorrow, Booking.status == "confirmed")
        .order_by(Booking.start_time)
        .all()
    )

    if not bookings:
        return

    housekeeping_list: list = []
    it_list:           list = []
    stationery_list:   list = []
    canteen_list:      list = []

    for b, h in bookings:
        coord_info = f"{b.coordinator_name or b.booked_by} ({b.coordinator_phone or 'N/A'})"

        housekeeping_list.append({
            "Hall":                  h.name,
            "Timings":               f"{b.start_time} - {b.end_time}",
            "Expected Attendees":    str(b.attendees_count) if b.attendees_count else "N/A",
            "Housekeeping Required": "Yes" if b.housekeeping_requested else "No",
            "Coordinator":           coord_info,
        })

        features_desc = b.features_requested or "None"
        if b.virtual_meeting_requested:
            features_desc += f" | Virtual Link: {b.meeting_link or 'Pending'}"

        it_list.append({
            "Hall":              h.name,
            "Timings":           f"{b.start_time} - {b.end_time}",
            "IT Staff Required": "Yes" if b.support_staff_requested else "No",
            "Hardware / AV":     features_desc,
            "Coordinator":       coord_info,
        })

        if b.stationery_requested:
            stationery_list.append({
                "Hall":                h.name,
                "Timings":             f"{b.start_time} - {b.end_time}",
                "Items Requested":     b.stationery_requested,
                "Hardware / Features": b.features_requested or "None",
                "Coordinator":         coord_info,
            })

        if b.food_requested:
            canteen_list.append({
                "Hall":                    h.name,
                "Timings":                 f"{b.start_time} - {b.end_time}",
                "Expected Attendees":      str(b.attendees_count) if b.attendees_count else "N/A",
                "Catering / Refreshments": b.food_requested,
                "Coordinator":             coord_info,
            })

    # Read recipients from settings
    hk_email = get_setting(db, "email_housekeeping", DEPARTMENT_EMAILS["housekeeping"])
    it_email = get_setting(db, "email_it",           DEPARTMENT_EMAILS["it"])
    st_email = get_setting(db, "email_stationery",   DEPARTMENT_EMAILS["stationery"])
    cn_email = get_setting(db, "email_canteen",       DEPARTMENT_EMAILS["canteen"])

    pretty_date = tomorrow.strftime("%A, %d %B %Y")
    total       = len(bookings)
    count_str   = f"{total} booking{'s' if total != 1 else ''} scheduled"

    def _sched_body(heading: str, intro: str, table_html: str, footer: str) -> str:
        """Build a standard department schedule email body."""
        return (
            _section_heading(heading)
            + f"<p style='font-size:13px;color:{_TEXT_LIGHT};margin:4px 0 0;'>{count_str}</p>"
            + f"<p style='margin:16px 0 8px;font-size:14px;color:{_TEXT_MID};"
              f"line-height:1.7;'>{intro}</p>"
            + _divider()
            + table_html
            + _divider()
            + f"<p style='font-size:13px;color:{_TEXT_LIGHT};margin:0;'>{footer}</p>"
        )

    # 1. Housekeeping Notification
    tpl_hk   = get_setting(db, "template_housekeeping", "")
    table_hk = format_meeting_rows(
        housekeeping_list,
        ["Hall", "Timings", "Expected Attendees", "Housekeeping Required", "Coordinator"]
    )
    if tpl_hk:
        try:
            hk_inner = tpl_hk.format(date=tomorrow.isoformat(), table=table_hk)
        except Exception:
            hk_inner = f"{tpl_hk}\n{table_hk}"
    else:
        hk_inner = _sched_body(
            "Housekeeping Daily Schedule",
            (f"Please find below the confirmed hall booking schedule for "
             f"<strong>{pretty_date}</strong>. Kindly ensure that each venue is set up "
             f"and cleaned according to the expected attendee counts and any special "
             f"housekeeping requests listed below."),
            table_hk,
            ("This schedule is generated automatically each evening for the following day. "
             "Please contact the listed coordinator directly for any clarifications.")
        )
    send_email(
        hk_email,
        f"Housekeeping Daily Schedule - {pretty_date}",
        _base_layout(f"Housekeeping schedule for {pretty_date}", hk_inner),
        db=db
    )

    # 2. IT Support Notification
    tpl_it   = get_setting(db, "template_it", "")
    table_it = format_meeting_rows(
        it_list,
        ["Hall", "Timings", "IT Staff Required", "Hardware / AV", "Coordinator"]
    )
    if tpl_it:
        try:
            it_inner = tpl_it.format(date=tomorrow.isoformat(), table=table_it)
        except Exception:
            it_inner = f"{tpl_it}\n{table_it}"
    else:
        it_inner = _sched_body(
            "IT Support Daily Schedule",
            (f"Please find below tomorrow's (<strong>{pretty_date}</strong>) confirmed hall "
             f"bookings that require IT attention, including hardware and AV setup and virtual "
             f"meeting configuration. Kindly ensure that all requested equipment is tested "
             f"and ready before each session begins."),
            table_it,
            ("Reach out to the session coordinator directly if you need additional details "
             "about hardware or connectivity requirements.")
        )
    send_email(
        it_email,
        f"IT Support Daily Schedule - {pretty_date}",
        _base_layout(f"IT support schedule for {pretty_date}", it_inner),
        db=db
    )

    # 3. Stationery Notification
    if stationery_list:
        tpl_st   = get_setting(db, "template_stationery", "")
        table_st = format_meeting_rows(
            stationery_list,
            ["Hall", "Timings", "Items Requested", "Hardware / Features", "Coordinator"]
        )
        if tpl_st:
            try:
                st_inner = tpl_st.format(date=tomorrow.isoformat(), table=table_st)
            except Exception:
                st_inner = f"{tpl_st}\n{table_st}"
        else:
            st_inner = _sched_body(
                "Stationery Requirements - Daily Schedule",
                (f"The following hall sessions scheduled for <strong>{pretty_date}</strong> "
                 f"have specific stationery requirements. Please ensure that the listed items "
                 f"are prepared and delivered to the respective halls prior to the start of "
                 f"each session."),
                table_st,
                ("Contact the session coordinator for any queries regarding quantities or "
                 "specific item preferences.")
            )
        send_email(
            st_email,
            f"Stationery Requirements - {pretty_date}",
            _base_layout(f"Stationery requirements for {pretty_date}", st_inner),
            db=db
        )

    # 4. Canteen / Catering Notification
    if canteen_list:
        tpl_cn   = get_setting(db, "template_canteen", "")
        table_cn = format_meeting_rows(
            canteen_list,
            ["Hall", "Timings", "Expected Attendees", "Catering / Refreshments", "Coordinator"]
        )
        if tpl_cn:
            try:
                cn_inner = tpl_cn.format(date=tomorrow.isoformat(), table=table_cn)
            except Exception:
                cn_inner = f"{tpl_cn}\n{table_cn}"
        else:
            cn_inner = _sched_body(
                "Catering and Refreshments - Daily Schedule",
                (f"The following hall sessions on <strong>{pretty_date}</strong> have requested "
                 f"catering or refreshment arrangements. Please plan and prepare accordingly to "
                 f"ensure timely delivery to each hall before the session commences."),
                table_cn,
                ("Kindly liaise with the session coordinator for any specific dietary preferences "
                 "or last-minute changes.")
            )
        send_email(
            cn_email,
            f"Catering and Refreshments Schedule - {pretty_date}",
            _base_layout(f"Catering requirements for {pretty_date}", cn_inner),
            db=db
        )


SENT_REMINDERS: set = set()


def send_upcoming_reminders(db: Session):
    import datetime
    now   = datetime.datetime.now()
    today = now.date()

    bookings = (
        db.query(Booking, Hall)
        .join(Hall, Booking.hall_id == Hall.id)
        .filter(
            Booking.booking_date == today,
            Booking.status == "confirmed",
            Booking.reminder_sent == False,
            (Booking.support_staff_requested == True) | (Booking.housekeeping_requested == True)
        )
        .all()
    )

    for b, h in bookings:
        try:
            b_start    = datetime.datetime.strptime(b.start_time, "%H:%M").time()
            b_start_dt = datetime.datetime.combine(today, b_start)
        except Exception:
            continue

        diff = b_start_dt - now
        if not (datetime.timedelta(minutes=0) <= diff <= datetime.timedelta(minutes=15, seconds=30)):
            continue

        coord_info  = f"{b.coordinator_name or b.booked_by} ({b.coordinator_phone or 'N/A'})"
        pretty_date = today.strftime("%A, %d %B %Y")

        def _reminder_body(dept_name: str, action_msg: str) -> str:
            return (
                _section_heading(f"{dept_name} - Upcoming Meeting Reminder")
                + _divider()
                + _info_box(
                    f"<strong>Action Required:</strong> {action_msg}",
                    color=_WARN_COLOR
                )
                + _detail_table(
                    _detail_row("Hall / Venue", h.name, highlight=True),
                    _detail_row("Date",         pretty_date),
                    _detail_row("Time",         f"{b.start_time} - {b.end_time}"),
                    _detail_row("Purpose",      b.purpose or "N/A"),
                    _detail_row("Coordinator",  coord_info),
                )
                + _divider()
                + (f"<p style='font-size:13px;color:{_TEXT_LIGHT};margin:0;'>"
                   f"This reminder was triggered automatically 15 minutes before the scheduled "
                   f"start time. Contact the coordinator listed above for last-minute changes.</p>")
            )

        if b.support_staff_requested:
            it_email = get_setting(db, "email_it", "it-support@icmr-nitvar.res.in")
            subject  = f"IT Support Reminder - Meeting in {h.name} starts in 15 minutes"
            body     = _reminder_body(
                "IT Support",
                "A meeting that requires IT support is starting in approximately "
                "<strong>15 minutes</strong>. Please ensure all required equipment "
                "is set up and operational before the session begins."
            )
            send_email(it_email, subject, _base_layout(subject, body), db=db)

        if b.housekeeping_requested:
            hk_email = get_setting(db, "email_housekeeping", "housekeeping@icmr-nitvar.res.in")
            subject  = f"Housekeeping Reminder - Meeting in {h.name} starts in 15 minutes"
            body     = _reminder_body(
                "Housekeeping",
                "A meeting that requires housekeeping attendance is starting in approximately "
                "<strong>15 minutes</strong>. Please ensure the hall is fully prepared "
                "and ready to receive attendees."
            )
            send_email(hk_email, subject, _base_layout(subject, body), db=db)

        b.reminder_sent = True
        db.commit()


def send_director_approval_request(db: Session, booking: Booking, hall: Hall):
    director_email = get_setting(db, "director_email", "director@icmr-nitvar.res.in")
    base_url       = get_setting(db, "base_url", "http://localhost:8000").rstrip("/")
    approve_url    = f"{base_url}/api/bookings/approve-by-token?token={booking.approval_token}"
    reject_url     = f"{base_url}/api/bookings/reject-by-token?token={booking.approval_token}"

    pretty_date = booking.booking_date.strftime("%A, %d %B %Y")
    subject     = f"Director Approval Required - {hall.name} Booking on {pretty_date}"

    booked_by_str = booking.booked_by
    if booking.scientist_designation:
        booked_by_str += f", {booking.scientist_designation}"
    if booking.dept:
        booked_by_str += f" | {booking.dept}"

    coord_parts = [booking.coordinator_name or "N/A"]
    if booking.coordinator_phone:
        coord_parts.append(booking.coordinator_phone)
    if booking.coordinator_email:
        coord_parts.append(booking.coordinator_email)
    coord_str = " &bull; ".join(coord_parts)

    body = (
        _section_heading("Booking Approval Request")
        + _divider()
        + (f"<p style='margin:0 0 16px;font-size:14px;color:{_TEXT_MID};line-height:1.7;'>"
           f"A new booking request has been submitted for a <strong>premium hall</strong> that "
           f"requires your approval before it can be confirmed. Please review the details below "
           f"and take the appropriate action.</p>")
        + _detail_table(
            _detail_row("Hall / Venue",       hall.name, highlight=True),
            _detail_row("Date",               pretty_date),
            _detail_row("Time",               f"{booking.start_time} - {booking.end_time}"),
            _detail_row("Booked By",          booked_by_str),
            _detail_row("Coordinator",        coord_str),
            _detail_row("Purpose",            booking.purpose or "N/A"),
            _detail_row("Expected Attendees", str(booking.attendees_count) if booking.attendees_count else "N/A"),
        )
        + _divider()
        + (f"<p style='font-size:14px;font-weight:600;color:{_TEXT_MID};margin:0 0 14px;'>"
           f"Please click one of the buttons below to take action:</p>")
        + ("<table cellpadding='0' cellspacing='0' border='0'><tr>"
           f"<td style='padding-right:12px;'>{_cta_button('Approve Booking', approve_url, _SUCCESS_COLOR)}</td>"
           f"<td>{_cta_button('Reject Booking', reject_url, _DANGER_COLOR)}</td>"
           "</tr></table>")
        + _divider()
        + (f"<p style='font-size:12px;color:{_TEXT_LIGHT};margin:0;line-height:1.6;'>"
           f"If the buttons above do not work, copy and paste the following links into your browser:<br/>"
           f"<strong>Approve:</strong> {approve_url}<br/>"
           f"<strong>Reject:</strong> {reject_url}</p>")
    )
    send_email(director_email, subject, _base_layout(subject, body), db=db)


def send_booking_confirmation(db: Session, booking: Booking, hall: Hall):
    if not booking.coordinator_email:
        return

    pretty_date  = booking.booking_date.strftime("%A, %d %B %Y")
    subject      = f"Booking Confirmed - {hall.name} on {pretty_date}"
    display_name = booking.coordinator_name or booking.booked_by

    virtual_section = ""
    if booking.virtual_meeting_requested and booking.meeting_link:
        virtual_section = (
            _divider()
            + (f"<p style='margin:0 0 8px;font-size:14px;font-weight:600;color:{_TEXT_MID};'>"
               f"Virtual Meeting Link</p>")
            + _info_box(
                f"Your virtual meeting link is ready: "
                f"<a href='{booking.meeting_link}' "
                f"style='color:{_BRAND_COLOR};font-weight:600;'>{booking.meeting_link}</a>",
                color=_BRAND_COLOR
            )
        )

    body = (
        _section_heading("Booking Confirmed")
        + _divider()
        + (f"<p style='margin:0 0 16px;font-size:15px;color:{_TEXT_MID};line-height:1.7;'>"
           f"Dear <strong>{display_name}</strong>,</p>")
        + (f"<p style='margin:0 0 16px;font-size:14px;color:{_TEXT_MID};line-height:1.7;'>"
           f"We are pleased to inform you that your hall booking request has been "
           f"<strong style='color:{_SUCCESS_COLOR};'>successfully confirmed</strong>. "
           f"Please find the details of your booking below.</p>")
        + _detail_table(
            _detail_row("Hall / Venue", hall.name, highlight=True),
            _detail_row("Date",         pretty_date),
            _detail_row("Time",         f"{booking.start_time} - {booking.end_time}"),
            _detail_row("Booked By",    booking.booked_by),
            _detail_row("Purpose",      booking.purpose or "N/A"),
        )
        + _divider()
        + _info_box(
            f"Your unique <strong>cancellation code</strong> is: "
            f"<strong style='font-size:18px;letter-spacing:2px;color:{_BRAND_DARK};'>"
            f"{booking.cancel_code}</strong><br/>"
            f"<span style='font-size:12px;'>Please keep this code safe &mdash; you will need "
            f"it to cancel or modify your booking.</span>",
            color=_SUCCESS_COLOR
        )
        + virtual_section
        + _divider()
        + (f"<p style='font-size:14px;color:{_TEXT_MID};line-height:1.7;margin:0;'>"
           f"If you need to cancel or make changes to this booking, please use the Hall Booking "
           f"System and provide the cancellation code above. For urgent assistance, contact the "
           f"administrative office directly.</p>")
        + (f"<p style='font-size:14px;color:{_TEXT_MID};margin:16px 0 0;'>"
           f"We wish you a productive and successful session.</p>")
    )
    send_email(booking.coordinator_email, subject, _base_layout(subject, body), db=db)


def send_booking_rejection(db: Session, booking: Booking, hall: Hall):
    if not booking.coordinator_email:
        return

    pretty_date  = booking.booking_date.strftime("%A, %d %B %Y")
    subject      = f"Booking Request Not Approved - {hall.name} on {pretty_date}"
    display_name = booking.coordinator_name or booking.booked_by

    body = (
        _section_heading("Booking Request Not Approved")
        + _divider()
        + (f"<p style='margin:0 0 16px;font-size:15px;color:{_TEXT_MID};line-height:1.7;'>"
           f"Dear <strong>{display_name}</strong>,</p>")
        + (f"<p style='margin:0 0 16px;font-size:14px;color:{_TEXT_MID};line-height:1.7;'>"
           f"We regret to inform you that your hall booking request has "
           f"<strong style='color:{_DANGER_COLOR};'>not been approved</strong> at this time. "
           f"The details of the declined request are provided below for your reference.</p>")
        + _detail_table(
            _detail_row("Hall / Venue", hall.name),
            _detail_row("Date",         pretty_date),
            _detail_row("Time",         f"{booking.start_time} - {booking.end_time}"),
            _detail_row("Booked By",    booking.booked_by),
            _detail_row("Purpose",      booking.purpose or "N/A"),
        )
        + _divider()
        + _info_box(
            "If you believe this decision was made in error, or if you require further information "
            "regarding the reason for this outcome, please contact the Director's Office or the "
            "administrative team directly.",
            color=_WARN_COLOR
        )
        + (f"<p style='font-size:14px;color:{_TEXT_MID};line-height:1.7;margin:16px 0 0;'>"
           f"You are welcome to submit a new booking request for an alternative date or time slot. "
           f"We apologise for any inconvenience this may have caused.</p>")
    )
    send_email(booking.coordinator_email, subject, _base_layout(subject, body), db=db)

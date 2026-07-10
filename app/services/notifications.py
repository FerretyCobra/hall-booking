from datetime import date, timedelta
from sqlalchemy.orm import Session
from ..models import Booking, Hall
from ..config import DEPARTMENT_EMAILS
from .email import send_email
from .settings import get_setting

def format_meeting_rows(meetings, cols):
    """Utility to format meetings as an HTML table."""
    if not meetings:
        return "<p>No meetings scheduled for tomorrow.</p>"
        
    th_html = "".join(f"<th style='border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;'>{col}</th>" for col in cols)
    
    rows_html = ""
    for m in meetings:
        tds = ""
        for key in cols:
            val = m.get(key, "")
            tds += f"<td style='border: 1px solid #ddd; padding: 8px;'>{val}</td>"
        rows_html += f"<tr>{tds}</tr>"
        
    return f"""
    <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
        <thead><tr>{th_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """

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
        # No bookings scheduled
        return
        
    # Prepare data lists
    housekeeping_list = []
    it_list = []
    stationery_list = []
    canteen_list = []
    
    for b, h in bookings:
        coord_info = f"{b.coordinator_name or b.booked_by} ({b.coordinator_phone or 'N/A'})"
        
        # Housekeeping: Hall, timings, attendees, coordinator
        housekeeping_list.append({
            "Hall": h.name,
            "Timings": f"{b.start_time} - {b.end_time}",
            "Attendees": b.attendees_count or "N/A",
            "Housekeeping Presence": "Requested" if b.housekeeping_requested else "No",
            "Coordinator": coord_info
        })
        
        # IT Staff: Hall, timings, support status, requested features, coordinator
        features_desc = b.features_requested or "None"
        if b.virtual_meeting_requested:
            meet_link_desc = f"Virtual Meet Link: {b.meeting_link or 'Pending approval'}"
            features_desc += f" | {meet_link_desc}"
            
        it_list.append({
            "Hall": h.name,
            "Timings": f"{b.start_time} - {b.end_time}",
            "IT Support Staff": "Requested" if b.support_staff_requested else "No",
            "Hardware/Features": features_desc,
            "Coordinator": coord_info
        })
        
        # Stationery: Hall, timings, hardware/features requested, coordinator
        if b.stationery_requested:
            stationery_list.append({
                "Hall": h.name,
                "Timings": f"{b.start_time} - {b.end_time}",
                "Requested Features": b.features_requested or "None",
                "Requested Stationery": b.stationery_requested,
                "Coordinator": coord_info
            })
        
        # Canteen: Hall, timings, expected attendees, coordinator
        if b.food_requested:
            canteen_list.append({
                "Hall": h.name,
                "Timings": f"{b.start_time} - {b.end_time}",
                "Expected Attendees": b.attendees_count or "N/A",
                "Catering / Refreshments": b.food_requested,
                "Coordinator": coord_info
            })
        
    # Read recipients & templates from settings
    hk_email = get_setting(db, "email_housekeeping", DEPARTMENT_EMAILS["housekeeping"])
    it_email = get_setting(db, "email_it", DEPARTMENT_EMAILS["it"])
    st_email = get_setting(db, "email_stationery", DEPARTMENT_EMAILS["stationery"])
    cn_email = get_setting(db, "email_canteen", DEPARTMENT_EMAILS["canteen"])

    tpl_hk = get_setting(db, "template_housekeeping", "<h2>Housekeeping Daily Schedule</h2>\n<p>Please find below the hall booking schedule for tomorrow (<strong>{date}</strong>) to assist with room setup and layout planning.</p>\n{table}")
    tpl_it = get_setting(db, "template_it", "<h2>IT Support Daily Schedule</h2>\n<p>Please find below the hall booking schedule for tomorrow (<strong>{date}</strong>) detailing requested IT presence and hardware features.</p>\n{table}")
    tpl_st = get_setting(db, "template_stationery", "<h2>Stationery Requirements Daily Schedule</h2>\n<p>Please find below the stationery and hardware requests for tomorrow's hall bookings (<strong>{date}</strong>).</p>\n{table}")
    tpl_cn = get_setting(db, "template_canteen", "<h2>Canteen Attendance Daily Schedule</h2>\n<p>Please find below the expected attendee counts and catering requests for tomorrow's meetings (<strong>{date}</strong>) to assist with canteen logistics and catering.</p>\n{table}")

    # 1. Housekeeping Notification
    table_hk = format_meeting_rows(housekeeping_list, ["Hall", "Timings", "Attendees", "Housekeeping Presence", "Coordinator"])
    try:
        housekeeping_html = tpl_hk.format(date=tomorrow.isoformat(), table=table_hk)
    except Exception:
        housekeeping_html = f"{tpl_hk}\n{table_hk}"
    send_email(hk_email, f"Housekeeping Daily Schedule - {tomorrow.isoformat()}", housekeeping_html, db=db)
    
    # 2. IT Staff Notification
    table_it = format_meeting_rows(it_list, ["Hall", "Timings", "IT Support Staff", "Hardware/Features", "Coordinator"])
    try:
        it_html = tpl_it.format(date=tomorrow.isoformat(), table=table_it)
    except Exception:
        it_html = f"{tpl_it}\n{table_it}"
    send_email(it_email, f"IT Support Daily Schedule - {tomorrow.isoformat()}", it_html, db=db)
    
    # 3. Stationery Notification
    if stationery_list:
        table_st = format_meeting_rows(stationery_list, ["Hall", "Timings", "Requested Features", "Requested Stationery", "Coordinator"])
        try:
            stationery_html = tpl_st.format(date=tomorrow.isoformat(), table=table_st)
        except Exception:
            stationery_html = f"{tpl_st}\n{table_st}"
        send_email(st_email, f"Stationery Requirements Schedule - {tomorrow.isoformat()}", stationery_html, db=db)
    
    # 4. Canteen Notification
    if canteen_list:
        table_cn = format_meeting_rows(canteen_list, ["Hall", "Timings", "Expected Attendees", "Catering / Refreshments", "Coordinator"])
        try:
            canteen_html = tpl_cn.format(date=tomorrow.isoformat(), table=table_cn)
        except Exception:
            canteen_html = f"{tpl_cn}\n{table_cn}"
        send_email(cn_email, f"Canteen Daily Schedule - {tomorrow.isoformat()}", canteen_html, db=db)


SENT_REMINDERS = set()

def send_upcoming_reminders(db: Session):
    import datetime
    now = datetime.datetime.now()
    today = now.date()
    
    # Query confirmed bookings for today that have IT support or housekeeping requested
    bookings = (
        db.query(Booking, Hall)
        .join(Hall, Booking.hall_id == Hall.id)
        .filter(
            Booking.booking_date == today,
            Booking.status == "confirmed",
            (Booking.support_staff_requested == True) | (Booking.housekeeping_requested == True)
        )
        .all()
    )
    
    for b, h in bookings:
        if b.id in SENT_REMINDERS:
            continue
            
        try:
            b_start = datetime.datetime.strptime(b.start_time, "%H:%M").time()
            b_start_dt = datetime.datetime.combine(today, b_start)
        except Exception:
            continue
            
        diff = b_start_dt - now
        # Check if start time is within 15 minutes (between 0 and 15 minutes, 30 seconds)
        if datetime.timedelta(minutes=0) <= diff <= datetime.timedelta(minutes=15, seconds=30):
            coord_info = f"{b.coordinator_name or b.booked_by} ({b.coordinator_phone or 'N/A'})"
            
            if b.support_staff_requested:
                it_email = get_setting(db, "email_it", "it-support@icmr-nitvar.res.in")
                subject = f"⚠️ IT Reminder: Meeting starting in 15 mins in {h.name}"
                body = f"""
                <h3>IT Support Reminder</h3>
                <p>This is a reminder that a meeting requiring IT presence is starting in 15 minutes.</p>
                <p><strong>Hall:</strong> {h.name}</p>
                <p><strong>Time:</strong> {b.start_time} - {b.end_time}</p>
                <p><strong>Coordinator:</strong> {coord_info}</p>
                <p><strong>Purpose:</strong> {b.purpose or 'N/A'}</p>
                """
                send_email(it_email, subject, body, db=db)
                
            if b.housekeeping_requested:
                hk_email = get_setting(db, "email_housekeeping", "housekeeping@icmr-nitvar.res.in")
                subject = f"⚠️ Housekeeping Reminder: Meeting starting in 15 mins in {h.name}"
                body = f"""
                <h3>Housekeeping Reminder</h3>
                <p>This is a reminder that a meeting requiring Housekeeping presence is starting in 15 minutes.</p>
                <p><strong>Hall:</strong> {h.name}</p>
                <p><strong>Time:</strong> {b.start_time} - {b.end_time}</p>
                <p><strong>Coordinator:</strong> {coord_info}</p>
                <p><strong>Purpose:</strong> {b.purpose or 'N/A'}</p>
                """
                send_email(hk_email, subject, body, db=db)
                
            SENT_REMINDERS.add(b.id)


def send_director_approval_request(db: Session, booking: Booking, hall: Hall):
    director_email = get_setting(db, "director_email", "director@icmr-nitvar.res.in")
    subject = f"📋 Director Approval Required: {hall.name} - {booking.booking_date.isoformat()}"
    
    base_url = get_setting(db, "base_url", "http://localhost:8000").rstrip("/")
    
    approve_url = f"{base_url}/api/bookings/approve-by-token?token={booking.approval_token}"
    reject_url = f"{base_url}/api/bookings/reject-by-token?token={booking.approval_token}"
    
    body = f"""
    <h2>Booking Approval Request</h2>
    <p>A new booking request requires director approval for the premium hall: <strong>{hall.name}</strong>.</p>
    <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Date:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.booking_date.isoformat()}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Time:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.start_time} - {booking.end_time}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Booked By:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.booked_by} ({booking.scientist_designation or 'N/A'}, {booking.dept or 'N/A'})</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Coordinator:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.coordinator_name or 'N/A'} ({booking.coordinator_phone or 'N/A'}, {booking.coordinator_email or 'N/A'})</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Purpose:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.purpose or 'N/A'}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Attendees Count:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.attendees_count or 'N/A'}</td></tr>
    </table>
    <p style='margin-top: 20px;'>
        <a href="{approve_url}" style="background-color: #22c55e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px; display: inline-block;">Approve Booking</a>
        <a href="{reject_url}" style="background-color: #dc2626; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Reject Booking</a>
    </p>
    """
    send_email(director_email, subject, body, db=db)


def send_booking_confirmation(db: Session, booking: Booking, hall: Hall):
    if not booking.coordinator_email:
        return
    subject = f"✅ Booking Confirmed: {hall.name} - {booking.booking_date.isoformat()}"
    
    meet_desc = ""
    if booking.virtual_meeting_requested:
        meet_desc = f"<p><strong>Virtual Meeting Link:</strong> <a href='{booking.meeting_link}'>{booking.meeting_link}</a></p>"
        
    body = f"""
    <h2>Booking Confirmed</h2>
    <p>Dear {booking.coordinator_name or booking.booked_by},</p>
    <p>Your booking request for <strong>{hall.name}</strong> has been successfully confirmed.</p>
    <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Date:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.booking_date.isoformat()}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Time:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{booking.start_time} - {booking.end_time}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Unique Cancel Code:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'><strong>{booking.cancel_code}</strong></td></tr>
    </table>
    {meet_desc}
    <p>Thank you.</p>
    """
    send_email(booking.coordinator_email, subject, body, db=db)


def send_booking_rejection(db: Session, booking: Booking, hall: Hall):
    if not booking.coordinator_email:
        return
    subject = f"❌ Booking Declined: {hall.name} - {booking.booking_date.isoformat()}"
    body = f"""
    <h2>Booking Request Declined</h2>
    <p>Dear {booking.coordinator_name or booking.booked_by},</p>
    <p>Unfortunately, your booking request for <strong>{hall.name}</strong> on {booking.booking_date.isoformat()} ({booking.start_time} - {booking.end_time}) has been declined.</p>
    <p>Thank you.</p>
    """
    send_email(booking.coordinator_email, subject, body, db=db)

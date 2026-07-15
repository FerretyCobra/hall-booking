import uuid
import os
import base64
import json
import urllib.request
import urllib.parse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from .. import config

logger = logging.getLogger(__name__)

class MeetingProvider:
    def create_meeting(self, booking_id: int, purpose: str) -> str:
        raise NotImplementedError()


class MockMeetingProvider(MeetingProvider):
    def create_meeting(self, booking_id: int, purpose: str) -> str:
        meeting_id = uuid.uuid4().hex[:12]
        return f"https://meet.mock.com/room/{meeting_id}"


class ZoomMeetingProvider(MeetingProvider):
    def get_access_token(self) -> str:
        account_id = config.ZOOM_ACCOUNT_ID
        client_id = config.ZOOM_CLIENT_ID
        client_secret = config.ZOOM_CLIENT_SECRET
        
        if not all([account_id, client_id, client_secret]):
            raise ValueError(
                "Zoom S2S credentials missing. Please configure ZOOM_ACCOUNT_ID, "
                "ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET in your environment."
            )
            
        url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
        
        req = urllib.request.Request(
            url,
            method="POST",
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "access_token" not in data:
                    raise KeyError("access_token not found in response")
                return data["access_token"]
        except Exception as e:
            logger.error(f"Failed to fetch Zoom access token: {e}")
            raise RuntimeError(f"Zoom OAuth token fetch failed: {e}")

    def create_meeting(self, booking_id: int, purpose: str) -> str:
        token = self.get_access_token()
        url = "https://api.zoom.us/v2/users/me/meetings"
        
        # We can dynamically retrieve the booking schedule times if we query the database
        start_time_iso = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        duration = 60
        
        try:
            from ..database import SessionLocal
            from ..models import Booking
            db = SessionLocal()
            try:
                booking = db.query(Booking).filter(Booking.id == booking_id).first()
                if booking:
                    # Parse local start and end times to calculate duration
                    date_str = booking.booking_date.strftime("%Y-%m-%d")
                    start_time_iso = f"{date_str}T{booking.start_time}:00Z"
                    
                    try:
                        t1 = datetime.strptime(booking.start_time, "%H:%M")
                        t2 = datetime.strptime(booking.end_time, "%H:%M")
                        duration = int((t2 - t1).total_seconds() / 60)
                    except Exception:
                        pass
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not retrieve booking details from database for Zoom meeting creation: {e}")

        body = {
            "topic": purpose,
            "type": 2,  # Scheduled meeting
            "start_time": start_time_iso,
            "duration": duration,
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": True
            }
        }
        
        req = urllib.request.Request(
            url,
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "join_url" not in data:
                    raise KeyError("join_url not found in response")
                return data["join_url"]
        except Exception as e:
            logger.error(f"Failed to create Zoom meeting: {e}")
            raise RuntimeError(f"Zoom create meeting failed: {e}")


class GoogleMeetProvider(MeetingProvider):
    def get_access_token(self) -> str:
        client_id = config.GOOGLE_CLIENT_ID
        client_secret = config.GOOGLE_CLIENT_SECRET
        refresh_token = config.GOOGLE_REFRESH_TOKEN
        
        if not all([client_id, client_secret, refresh_token]):
            raise ValueError(
                "Google credentials missing. Please configure GOOGLE_CLIENT_ID, "
                "GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in your environment."
            )
            
        url = "https://oauth2.googleapis.com/token"
        payload = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            method="POST",
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "access_token" not in data:
                    raise KeyError("access_token not found in response")
                return data["access_token"]
        except Exception as e:
            logger.error(f"Failed to fetch Google access token: {e}")
            raise RuntimeError(f"Google OAuth token refresh failed: {e}")

    def create_meeting(self, booking_id: int, purpose: str) -> str:
        token = self.get_access_token()
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1"
        
        request_id = f"hall-booking-{booking_id}-{uuid.uuid4().hex[:8]}"
        
        # Default start and end times
        start_iso = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = (datetime.utcnow() + timedelta(hours=1, minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        try:
            from ..database import SessionLocal
            from ..models import Booking
            db = SessionLocal()
            try:
                booking = db.query(Booking).filter(Booking.id == booking_id).first()
                if booking:
                    date_str = booking.booking_date.strftime("%Y-%m-%d")
                    start_iso = f"{date_str}T{booking.start_time}:00"
                    end_iso = f"{date_str}T{booking.end_time}:00"
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not retrieve booking details from database for Google Calendar event: {e}")

        body = {
            "summary": purpose,
            "description": f"Auto-generated virtual meeting for Booking ID: {booking_id}",
            "start": {
                "dateTime": start_iso,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_iso,
                "timeZone": "UTC"
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": request_id,
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            }
        }
        
        req = urllib.request.Request(
            url,
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                
                # Check for Meet link in conferenceData
                conf_data = data.get("conferenceData", {})
                entry_points = conf_data.get("entryPoints", [])
                for ep in entry_points:
                    if ep.get("entryPointType") == "video":
                        return ep.get("uri")
                        
                # Fallback to HTML link if Meet specifically wasn't generated
                if "htmlLink" in data:
                    return data["htmlLink"]
                raise KeyError("Google Meet conference link not found in response")
        except Exception as e:
            logger.error(f"Failed to create Google Meet event: {e}")
            raise RuntimeError(f"Google Meet creation failed: {e}")


def get_active_meeting_provider() -> MeetingProvider:
    provider_name = config.ACTIVE_MEETING_PROVIDER
    if provider_name == "zoom":
        return ZoomMeetingProvider()
    elif provider_name == "google":
        return GoogleMeetProvider()
    else:
        return MockMeetingProvider()

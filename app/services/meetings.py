import uuid
import os
from typing import Dict, Any

class MeetingProvider:
    def create_meeting(self, booking_id: int, purpose: str) -> str:
        raise NotImplementedError()


class MockMeetingProvider(MeetingProvider):
    def create_meeting(self, booking_id: int, purpose: str) -> str:
        meeting_id = uuid.uuid4().hex[:12]
        return f"https://meet.mock.com/room/{meeting_id}"


class ZoomMeetingProvider(MeetingProvider):
    def create_meeting(self, booking_id: int, purpose: str) -> str:
        # In a real setup, this would exchange Zoom S2S OAuth credentials
        # and POST to https://api.zoom.us/v2/users/me/meetings.
        # We stub this out with a Zoom-like URL structure for demonstration.
        meeting_id = "".join(filter(str.isdigit, str(uuid.uuid4().int)))[:11]
        pwd = uuid.uuid4().hex[:8]
        return f"https://zoom.us/j/{meeting_id}?pwd={pwd}"


class GoogleMeetProvider(MeetingProvider):
    def create_meeting(self, booking_id: int, purpose: str) -> str:
        # In a real setup, this would authenticate using service account credentials
        # and call the Google Calendar API with conferenceDataVersion=1.
        # We stub this out with a Google Meet-like URL structure.
        room_code = f"{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:3]}"
        return f"https://meet.google.com/{room_code}"


def get_active_meeting_provider() -> MeetingProvider:
    # Read provider choice from environment or fallback to mock
    provider_name = os.environ.get("ACTIVE_MEETING_PROVIDER", "mock").lower()
    if provider_name == "zoom":
        return ZoomMeetingProvider()
    elif provider_name == "google":
        return GoogleMeetProvider()
    else:
        return MockMeetingProvider()

import os
import json
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Calendar scope
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authenticate_google_calendar():
    """
    Authenticate Google Calendar using Service Account (Render-safe)
    """

    if "GOOGLE_SERVICE_ACCOUNT_JSON" not in os.environ:
        raise RuntimeError("❌ GOOGLE_SERVICE_ACCOUNT_JSON env variable not set")

    service_account_info = json.loads(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    )

    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )

    service = build("calendar", "v3", credentials=credentials)
    return service


def create_event(
    service,
    person_name: str,
    date: str,
    time: str,
    duration_minutes: int = 60,
):
    """
    Creates Google Calendar event

    date: YYYY-MM-DD
    time: HH:MM (24-hour)
    """

    start_dt = datetime.fromisoformat(f"{date}T{time}")
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event = {
        "summary": f"Meeting with {person_name}",
        "description": "Scheduled via WhatsApp AI Calendar Bot",
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    print("📅 Event created:", created_event.get("htmlLink"))
    return created_event.get("htmlLink")

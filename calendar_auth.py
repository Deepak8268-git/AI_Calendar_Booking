from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os , json

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def authenticate_google_calendar():
    creds = None

    if os.path.exists("token.json"):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
        creds = flow.run_local_server(port=0)   

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


def create_event(service, event_data):
    """
    Creates an event in the primary calendar using the provided data.
    event_data should contain: summary, description, start_time, end_time, timezone
    """
    event = {
        "summary": event_data.get("summary", "AI Scheduled Meeting"),
        "description": event_data.get("description", "Created via AI_Calendar_Booking"),
        "start": {
            "dateTime": event_data["start_time"],
            "timeZone": event_data.get("timezone", "Asia/Kolkata"),
        },
        "end": {
            "dateTime": event_data["end_time"],
            "timeZone": event_data.get("timezone", "Asia/Kolkata"),
        },
    }

    event_result = service.events().insert(calendarId="primary", body=event).execute()
    print(f"📅 Event created: {event_result.get('htmlLink')}")
    return event_result


if __name__ == "__main__":
    service = authenticate_google_calendar()
    # create_event(service, {...})

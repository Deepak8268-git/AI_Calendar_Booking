from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from gemini_parser import extract_meeting_details
from calendar_auth import authenticate_google_calendar, create_event
import datetime
import time

app = Flask(__name__)

# In-memory multi-turn memory
# sender_number -> meeting data
pending_meetings = {}

TIMEOUT_SECONDS = 300  # 5 minutes


def cleanup_expired_meetings():
    """Remove expired pending meetings"""
    now = time.time()
    expired_users = [
        user for user, data in pending_meetings.items()
        if now - data["created_at"] > TIMEOUT_SECONDS
    ]
    for user in expired_users:
        del pending_meetings[user]


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    cleanup_expired_meetings()

    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From")

    print(f"📩 WhatsApp message from {sender}: {incoming_msg}")

    resp = MessagingResponse()
    msg_lower = incoming_msg.lower()

    # -------------------------------
    # 1️⃣ HANDLE EXISTING PENDING MEETING
    # -------------------------------
    if sender in pending_meetings:
        meeting = pending_meetings[sender]

        # YES / CONFIRM
        if msg_lower in ["yes", "confirm", "ok", "sure"]:
            start_dt = datetime.datetime.fromisoformat(
                f"{meeting['date']}T{meeting['time']}:00"
            )
            end_dt = start_dt + datetime.timedelta(hours=1)

            event_data = {
                "summary": meeting["summary"],
                "description": meeting["description"],
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "timezone": "Asia/Kolkata"
            }

            service = authenticate_google_calendar()
            create_event(service, event_data)

            resp.message(
                f"✅ Meeting scheduled!\n"
                f"👤 {meeting['summary']}\n"
                f"🗓 {meeting['date']}\n"
                f"⏰ {meeting['time']}"
            )

            del pending_meetings[sender]
            return str(resp)

        # CANCEL
        if msg_lower in ["no", "cancel"]:
            del pending_meetings[sender]
            resp.message("❌ Meeting request cancelled.")
            return str(resp)

        # User replying with missing info → re-run AI
        details = extract_meeting_details(incoming_msg)
        print(f"🧠 Follow-up extracted: {details}")

        if details.get("date"):
            meeting["date"] = details["date"]

        if details.get("time"):
            meeting["time"] = details["time"]

        # Ask for what is still missing
        if not meeting.get("date"):
            resp.message("📅 When should I schedule the meeting?")
            return str(resp)

        if not meeting.get("time"):
            resp.message("⏰ What time should I schedule it?")
            return str(resp)

        # Everything collected → ask confirmation
        resp.message(
            f"📌 Please confirm:\n\n"
            f"👤 {meeting['summary']}\n"
            f"🗓 {meeting['date']}\n"
            f"⏰ {meeting['time']}\n\n"
            f"Reply YES to confirm or CANCEL to stop."
        )
        return str(resp)

    # -------------------------------
    # 2️⃣ NEW MESSAGE → AI INTENT DETECTION
    # -------------------------------
    details = extract_meeting_details(incoming_msg)
    print(f"🧠 Extracted details: {details}")

    if not details or details.get("intent") != "schedule_meeting":
        resp.message(
            "🤖 I can help you schedule meetings.\n"
            "Try: *Meet Mr Rahul tomorrow at 4 PM*"
        )
        return str(resp)

    # -------------------------------
    # 3️⃣ STORE IN MEMORY (NOT CALENDAR)
    # -------------------------------
    pending_meetings[sender] = {
        "person_name": details.get("person_name"),
        "date": details.get("date"),
        "time": details.get("time"),
        "summary": f"Meeting with {details.get('person_name', 'Unknown')}",
        "description": f"WhatsApp Request: {incoming_msg}",
        "created_at": time.time()
    }

    # -------------------------------
    # 4️⃣ ASK FOR MISSING INFORMATION
    # -------------------------------
    if not details.get("date"):
        resp.message("📅 When should I schedule the meeting?")
        return str(resp)

    if not details.get("time"):
        resp.message("⏰ What time should I schedule it?")
        return str(resp)

    # -------------------------------
    # 5️⃣ ASK FOR CONFIRMATION
    # -------------------------------
    resp.message(
        f"📌 Please confirm your meeting:\n\n"
        f"👤 Meeting with {details.get('person_name')}\n"
        f"🗓 Date: {details.get('date')}\n"
        f"⏰ Time: {details.get('time')}\n\n"
        f"Reply YES to confirm or CANCEL to stop."
    )

    return str(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


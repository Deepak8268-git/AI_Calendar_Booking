from flask import Flask, request, Response
from gemini_parser import extract_meeting_details
from calendar_auth import authenticate_google_calendar, create_event
import os

app = Flask(__name__)

# 🔒 In-memory session store
pending_meetings = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From")

    msg_lower = incoming_msg.lower()

    # =======================
    # STEP 2: CONFIRMATION
    # =======================
    if from_number in pending_meetings:
        if msg_lower == "yes":
            data = pending_meetings.pop(from_number)

            service = authenticate_google_calendar()
            create_event(
                service,
                person_name=data["person_name"] or "Meeting",
                date=data["date"],
                time=data["time"]
            )

            return twiml("✅ Your meeting has been scheduled in Google Calendar.")

        if msg_lower == "no":
            pending_meetings.pop(from_number)
            return twiml("❌ Meeting cancelled.")

        # Waiting for YES/NO
        return twiml("⚠️ Please reply YES to confirm or NO to cancel.")

    # =======================
    # STEP 1: NEW MESSAGE
    # =======================
    details = extract_meeting_details(incoming_msg)

    if details["intent"] != "schedule_meeting":
        return twiml(
            "👋 Hi! You can say:\n"
            "“Meet Mr Rahul on 7th Feb at 4 PM”"
        )

    if not details["date"] or not details["time"]:
        return twiml("📅 Please provide both date and time.")

    # Save meeting for confirmation
    pending_meetings[from_number] = details

    return twiml(
        f"📅 *Meeting Details*\n"
        f"👤 {details['person_name']}\n"
        f"📆 {details['date']}\n"
        f"⏰ {details['time']}\n\n"
        f"Reply *YES* to confirm or *NO* to cancel."
    )


def twiml(message):
    return Response(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>""",
        mimetype="application/xml"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

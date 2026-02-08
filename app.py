from flask import Flask, request, Response
from gemini_parser import extract_meeting_details
from calendar_auth import authenticate_google_calendar, create_event
import os, json

app = Flask(__name__)

# 🧠 Temporary in-memory store (per phone number)
pending_meetings = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From")  # whatsapp:+91xxxx

    incoming_lower = incoming_msg.lower()

    # ---------- STEP 2: Confirmation ----------
    if from_number in pending_meetings:
        if incoming_lower == "yes":
            data = pending_meetings.pop(from_number)

            service = authenticate_google_calendar()
            create_event(
                service,
                person_name=data["person_name"] or "Unknown",
                date=data["date"],
                time=data["time"]
            )

            return twiml("✅ Your meeting has been confirmed and saved to Google Calendar.")

        elif incoming_lower == "no":
            pending_meetings.pop(from_number)
            return twiml("❌ Meeting cancelled.")

    # ---------- STEP 1: Parse new message ----------
    details = extract_meeting_details(incoming_msg)

    if details["intent"] != "schedule_meeting":
        return twiml(
            "👋 Hi! You can say:\n"
            "“Meet Mr Rahul on 7th Feb at 4 PM”"
        )

    # Missing date/time → ask follow-up
    if not details["date"] or not details["time"]:
        return twiml("📅 Please tell me the date and time for the meeting.")

    # Save pending meeting
    pending_meetings[from_number] = details

    reply = (
        f"📅 *Meeting Details:*\n"
        f"👤 {details['person_name']}\n"
        f"📆 {details['date']}\n"
        f"⏰ {details['time']}\n\n"
        f"Reply *YES* to confirm or *NO* to cancel."
    )

    return twiml(reply)


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

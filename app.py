from flask import Flask, request, Response
from gemini_parser import extract_meeting_details
from calendar_auth import authenticate_google_calendar, create_event
import os

app = Flask(__name__)

# 🔒 In-memory store (one user → one pending meeting)
pending_meetings = {}


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From")
    msg_lower = incoming_msg.lower()

    # ==================================================
    # STEP 2️⃣ : HANDLE CONFIRMATION (YES / NO)
    # ==================================================
    if from_number in pending_meetings:

        if msg_lower == "yes":
            meeting = pending_meetings.pop(from_number)

            try:
                service = authenticate_google_calendar()
                create_event(
                    service,
                    person_name=meeting["person_name"] or "Meeting",
                    date=meeting["date"],
                    time=meeting["time"]
                )

                return twiml(
                    "✅ Your meeting has been confirmed and saved to Google Calendar."
                )

            except Exception as e:
                return twiml(
                    "❌ Failed to save meeting to Google Calendar. Please try again later."
                )

        if msg_lower == "no":
            pending_meetings.pop(from_number)
            return twiml("❌ Meeting cancelled successfully.")

        # User sent something else while confirmation pending
        return twiml("⚠️ Please reply YES to confirm or NO to cancel.")

    # ==================================================
    # STEP 1️⃣ : NEW MESSAGE → GEMINI PARSING
    # ==================================================
    details = extract_meeting_details(incoming_msg)

    # No meeting intent
    if details["intent"] != "schedule_meeting":
        return twiml(
            "👋 Hi! You can say:\n"
            "“Meet Mr Rahul on 7th Feb at 4 PM”"
        )

    # Missing date or time
    if not details["date"] or not details["time"]:
        return twiml("📅 Please provide both date and time for the meeting.")

    # ==================================================
    # STEP 3️⃣ : ASK FOR CONFIRMATION
    # ==================================================
    pending_meetings[from_number] = details

    return twiml(
        f"📅 Meeting Details\n"
        f"👤 {details['person_name'] or 'Guest'}\n"
        f"📆 {details['date']}\n"
        f"⏰ {details['time']}\n\n"
        f"Reply YES to confirm or NO to cancel."
    )


# ==================================================
# TWILIO XML RESPONSE
# ==================================================
def twiml(message: str):
    return Response(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>""",
        mimetype="application/xml"
    )


# ==================================================
# RENDER ENTRY POINT
# ==================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

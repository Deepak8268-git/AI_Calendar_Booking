from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import datetime

from gemini_parser import extract_meeting_details
from calendar_auth import authenticate_google_calendar, create_event

app = Flask(__name__)

# 🔹 In-memory session storage (per WhatsApp number)
sessions = {}


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From")

    print(f"📩 Message from {sender}: {incoming_msg}")

    resp = MessagingResponse()

    msg_lower = incoming_msg.lower()

    # --------------------------------------------------
    # 1️⃣ HANDLE YES / NO CONFIRMATION
    # --------------------------------------------------
    if sender in sessions and sessions[sender]["awaiting_confirmation"]:

        if msg_lower in ["yes", "y"]:
            session = sessions[sender]

            service = authenticate_google_calendar()

            start_time = f"{session['date']}T{session['time']}:00"
            start_dt = datetime.datetime.fromisoformat(start_time)
            end_dt = start_dt + datetime.timedelta(hours=1)

            event_data = {
                "summary": f"Meeting with {session['person_name']}",
                "description": "Scheduled via WhatsApp AI Assistant",
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "timezone": "Asia/Kolkata"
            }

            create_event(service, event_data)

            resp.message(
                f"✅ Your meeting with {session['person_name']} "
                f"on {session['date']} at {session['time']} "
                f"has been added to Google Calendar."
            )

            del sessions[sender]
            return str(resp)

        elif msg_lower in ["no", "n", "cancel"]:
            resp.message("❌ Meeting cancelled. No event was created.")
            del sessions[sender]
            return str(resp)

        else:
            resp.message("Please reply YES to confirm or NO to cancel.")
            return str(resp)

    # --------------------------------------------------
    # 2️⃣ NEW MESSAGE → USE GEMINI
    # --------------------------------------------------
    details = extract_meeting_details(incoming_msg)
    print("🧠 Extracted:", details)

    if details["intent"] != "schedule_meeting":
        resp.message(
            "👋 Hi! You can say:\n"
            "“Meet Mr Rahul on 7th Feb at 4 PM”"
        )
        return str(resp)

    # If date or time missing → ask follow-up
    if not details["date"] or not details["time"]:
        resp.message(
            "⏰ I need both date and time.\n"
            "Example: “Tomorrow at 4 PM”"
        )
        return str(resp)

    # --------------------------------------------------
    # 3️⃣ STORE & ASK FOR CONFIRMATION
    # --------------------------------------------------
    sessions[sender] = {
        "awaiting_confirmation": True,
        "person_name": details["person_name"] or "Unknown",
        "date": details["date"],
        "time": details["time"]
    }

    resp.message(
        f"📅 Please confirm your meeting:\n\n"
        f"👤 Person: {details['person_name']}\n"
        f"📆 Date: {details['date']}\n"
        f"⏰ Time: {details['time']}\n\n"
        f"Reply YES to confirm or NO to cancel."
    )

    return str(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


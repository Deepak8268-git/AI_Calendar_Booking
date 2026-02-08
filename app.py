import os
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from collections import defaultdict

from gemini_parser import extract_meeting_details

# --------------------------------
# CREATE FLASK APP (THIS WAS MISSING)
# --------------------------------
app = Flask(__name__)

# Store user session data (in-memory)
user_sessions = defaultdict(dict)

# --------------------------------
# WHATSAPP WEBHOOK
# --------------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    from_number = request.form.get("From")
    incoming_msg = request.form.get("Body", "").strip().lower()

    resp = MessagingResponse()
    session = user_sessions[from_number]

    # -------------------------------
    # CONFIRMATION HANDLING
    # -------------------------------
    if incoming_msg in ["yes", "y"] and session.get("awaiting_confirmation"):
        resp.message("✅ Your meeting has been confirmed.")
        user_sessions[from_number] = {}
        return Response(str(resp), mimetype="application/xml")

    if incoming_msg in ["no", "n"] and session.get("awaiting_confirmation"):
        resp.message("❌ Meeting cancelled.")
        user_sessions[from_number] = {}
        return Response(str(resp), mimetype="application/xml")

    # -------------------------------
    # EXTRACT MEETING DETAILS
    # -------------------------------
    details = extract_meeting_details(incoming_msg)

    if details["intent"] != "schedule_meeting":
        resp.message("❓ I can help you schedule a meeting.")
        return Response(str(resp), mimetype="application/xml")

    # Save extracted data
    for key in ["person_name", "date", "time"]:
        if details.get(key):
            session[key] = details[key]

    # -------------------------------
    # ASK FOR MISSING INFO
    # -------------------------------
    if not session.get("person_name"):
        resp.message("👤 With whom is the meeting?")
        return Response(str(resp), mimetype="application/xml")

    if not session.get("date"):
        resp.message("📅 On which date should I schedule the meeting?")
        return Response(str(resp), mimetype="application/xml")

    if not session.get("time"):
        resp.message("⏰ At what time should I schedule the meeting?")
        return Response(str(resp), mimetype="application/xml")

    # -------------------------------
    # CONFIRMATION STEP
    # -------------------------------
    session["awaiting_confirmation"] = True

    resp.message(
        f"📅 Meeting Details:\n"
        f"👤 {session['person_name']}\n"
        f"📆 {session['date']}\n"
        f"⏰ {session['time']}\n\n"
        f"Reply YES to confirm or NO to cancel."
    )

    return Response(str(resp), mimetype="application/xml")


# --------------------------------
# RUN APP (RENDER NEEDS THIS)
# --------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

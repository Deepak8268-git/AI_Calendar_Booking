from flask import request, Response
from twilio.twiml.messaging_response import MessagingResponse
from gemini_parser import extract_meeting_details

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    from_number = request.form.get("From")
    incoming_msg = request.form.get("Body", "").strip().lower()

    resp = MessagingResponse()

    session = user_sessions[from_number]

    # YES / NO confirmation
    if incoming_msg in ["yes", "y"] and session.get("awaiting_confirmation"):
        session["confirmed"] = True
        session["awaiting_confirmation"] = False

        resp.message("✅ Your meeting has been confirmed.")
        user_sessions[from_number] = {}
        return Response(str(resp), mimetype="application/xml")

    if incoming_msg in ["no", "n"] and session.get("awaiting_confirmation"):
        resp.message("❌ Meeting cancelled.")
        user_sessions[from_number] = {}
        return Response(str(resp), mimetype="application/xml")

    # Extract info
    details = extract_meeting_details(incoming_msg)

    if details["intent"] != "schedule_meeting":
        resp.message("❓ I can help you schedule meetings.")
        return Response(str(resp), mimetype="application/xml")

    # Save extracted fields
    session.update({k: v for k, v in details.items() if v})

    # Ask missing info
    if not session.get("date"):
        resp.message("📅 On which date should I schedule the meeting?")
        return Response(str(resp), mimetype="application/xml")

    if not session.get("time"):
        resp.message("⏰ At what time should I schedule the meeting?")
        return Response(str(resp), mimetype="application/xml")

    if not session.get("person_name"):
        resp.message("👤 With whom is the meeting?")
        return Response(str(resp), mimetype="application/xml")

    # All details present → confirmation
    session["awaiting_confirmation"] = True

    resp.message(
        f"📅 Meeting Details:\n"
        f"👤 {session['person_name']}\n"
        f"📆 {session['date']}\n"
        f"⏰ {session['time']}\n\n"
        f"Reply YES to confirm or NO to cancel."
    )

    return Response(str(resp), mimetype="application/xml")

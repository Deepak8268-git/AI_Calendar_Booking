import os
import json
import time
import re
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not set")

URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-1.5-flash:generateContent?key={API_KEY}"
)

def extract_meeting_details(message: str):
    prompt = f"""
Extract meeting info and return ONLY JSON.

Format:
{{
  "intent": "schedule_meeting" | "none",
  "person_name": string | null,
  "date": "YYYY-MM-DD" | null,
  "time": "HH:MM" | null
}}

Message:
"{message}"
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    for attempt in range(3):
        try:
            response = requests.post(
                URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )

            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()

            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            match = re.search(r"\{.*\}", text, re.DOTALL)

            if match:
                return json.loads(match.group())

            return {"intent": "none", "person_name": None, "date": None, "time": None}

        except Exception as e:
            print(f"⚠️ Gemini attempt {attempt+1} failed:", e)
            time.sleep(2)

    # NEVER crash WhatsApp webhook
    return {"intent": "none", "person_name": None, "date": None, "time": None}

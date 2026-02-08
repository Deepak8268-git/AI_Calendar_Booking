import os
import json
import time
import re
import requests

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not set in environment variables")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-flash-latest:generateContent?key={API_KEY}"
)

def extract_meeting_details(message: str) -> dict:
    """
    Uses Gemini to extract meeting intent, person, date, and time
    """

    prompt = f"""
You are an information extraction engine.

Extract meeting information from the WhatsApp message below.

Return ONLY valid JSON in this exact format:

{{
  "intent": "schedule_meeting" | "none",
  "person_name": string | null,
  "date": "YYYY-MM-DD" | null,
  "time": "HH:MM" | null
}}

Rules:
- Convert relative dates like "tomorrow" correctly
- Convert time to 24-hour format
- If unclear, return null for that field
- Do NOT add explanations or text outside JSON

Message:
\"{message}\"
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    for attempt in range(3):
        response = requests.post(GEMINI_URL, json=payload, timeout=30)

        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue

        response.raise_for_status()

        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

        print("🧠 Gemini raw response:\n", raw_text)

        # Extract JSON safely
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return {
                "intent": "none",
                "person_name": None,
                "date": None,
                "time": None
            }

        return json.loads(match.group(0))

    raise RuntimeError("❌ Gemini API failed after retries")


# 🔍 LOCAL TEST
if __name__ == "__main__":
    test_messages = [
        "hi",
        "meet mr rahul on 9th march 2025 at 9 am",
        "I want to meet Mr Deepak",
        "schedule a meeting tomorrow at 4 pm"
    ]

    for msg in test_messages:
        print("\n📩 Message:", msg)
        print("📊 Parsed:", extract_meeting_details(msg))

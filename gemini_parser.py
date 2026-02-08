import os
import json
import time
import re
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-flash-latest:generateContent"
)

HEADERS = {"Content-Type": "application/json"}


def extract_meeting_details(message: str) -> dict:
    prompt = f"""
You are an information extraction engine.

Your task:
Extract meeting details from the message.
DO NOT ask questions.
DO NOT add explanations.
ONLY return valid JSON.

Rules:
- intent: "schedule_meeting" ONLY if message indicates meeting intent
- date/time may be partial or missing
- If user replies like "tomorrow", "today", treat it as date info
- confidence:
  - "complete" if person_name + date + time present
  - "partial" if some fields missing
  - "none" if no meeting intent

JSON format:
{{
  "intent": "schedule_meeting | none",
  "person_name": string | null,
  "date": "YYYY-MM-DD" | null,
  "time": "HH:MM" | null,
  "confidence": "complete | partial | none"
}}

Message:
"{message}"
"""

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    for attempt in range(5):
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers=HEADERS,
            json=payload,
            timeout=20
        )

        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue

        response.raise_for_status()

        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("Invalid Gemini response")

        return json.loads(match.group(0))

    raise RuntimeError("Gemini failed after retries")

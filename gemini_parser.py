import os
import json
import time
import re
import requests

# 🔐 Load API key from environment (MANDATORY for production)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not set in environment variables")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-flash-latest:generateContent"
)

HEADERS = {
    "Content-Type": "application/json"
}


def extract_meeting_details(message: str) -> dict:
    """
    Uses Gemini to extract meeting intent and details from WhatsApp text.
    Returns a dictionary with keys:
    intent, person_name, date, time
    """

    prompt = f"""
Extract meeting information from the WhatsApp message below.

Return ONLY valid JSON with these keys:
- intent: "schedule_meeting" or "none"
- person_name
- date (YYYY-MM-DD)
- time (HH:MM in 24-hour format)

If a value is missing, use null.

Message:
"{message}"
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    max_retries = 5
    base_delay = 2  # seconds

    for attempt in range(max_retries):
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers=HEADERS,
            json=payload,
            timeout=30
        )

        # 🔁 Retry on quota/rate limit
        if response.status_code == 429:
            wait_time = base_delay * (2 ** attempt)
            print(f"⚠️ Gemini rate-limited. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            continue

        response.raise_for_status()

        data = response.json()

        # 🧠 Safely extract model output
        try:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise ValueError("❌ Invalid response format from Gemini")

        # 🧹 Remove markdown/code blocks if present
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        json_text = match.group(0) if match else raw_text

        return json.loads(json_text)

    raise RuntimeError("❌ Gemini API failed after multiple retries")


# 🧪 Local test
if __name__ == "__main__":
    test_msg = "I want to meet Mr Rahul tomorrow at 4 PM"
    print(extract_meeting_details(test_msg))

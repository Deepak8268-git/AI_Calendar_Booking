import requests
import json

API_KEY = "AIzaSyCfMOLzU9FAa0oH0p0UTAFPhdIUeiBrPZ4"  # your real key

def extract_meeting_details(message):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-flash-latest:generateContent?key={API_KEY}"
    )

    prompt = f"""
    Extract meeting information from the WhatsApp message below.

    Return ONLY valid JSON with:
    - intent (schedule_meeting or none)
    - person_name
    - date (YYYY-MM-DD)
    - time (HH:MM in 24-hour format)

    If any value is missing, return null.

    Message:
    "{message}"
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    import time
    
    max_retries = 5
    base_delay = 2  # seconds

    for attempt in range(max_retries):
        response = requests.post(url, json=payload)
        
        if response.status_code == 429:
            wait_time = base_delay * (2 ** attempt)
            print(f"⚠️ Quota exceeded (429). Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
            continue
            
        response.raise_for_status()
        
        result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        # Clean markdown code blocks if present
        import re
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = result_text

        return json.loads(json_str)
    
    raise Exception("Failed to call Gemini API after multiple retries due to Rate Limiting (429).")
    
    
if __name__ == "__main__":
    msg = "I want to meet Mr Rahul tomorrow at 4 PM"
    print(extract_meeting_details(msg))

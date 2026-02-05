from gemini_parser import extract_meeting_details
from calendar_auth import authenticate_google_calendar, create_event
import datetime

def main():
    print("🤖 AI Calendar Booker initialized...")
    
    # 1. Get input (hardcoded for now as per first iteration)
    user_input = "Schedule a meeting with Client X tomorrow at 3 PM for project discussion"
    print(f"📝 Processing message: '{user_input}'")
    
    # 2. Parse with AI
    try:
        details = extract_meeting_details(user_input)
        print(f"🧠 Extracted Details: {details}")
        
        if not details or details.get("intent") != "schedule_meeting":
            print("❌ No valid meeting intent found.")
            return

        # 3. Format Date/Time for Google Calendar (Simple logic)
        # Assuming 'tomorrow' relative to today, and HH:MM format
        today = datetime.date.today()
        
        # Helper to parse date
        if details.get("date"):
            # Try to map 'YYYY-MM-DD' directly
            try:
                event_date = str(details['date'])
                # If AI returns relative terms or just day/month, this might need better parsing logic
                # For this MVP, we assume the AI returns YYYY-MM-DD correctly as instructed by system prompt
            except ValueError:
                print("❌ Invalid date format from AI")
                return
        else:
             # Fallback if AI fails (should strictly come from AI instruction)
             event_date = (today + datetime.timedelta(days=1)).isoformat()
        
        start_time_str = f"{event_date}T{details['time']}:00"
        
        # Calculate end time (default 1 hour duration)
        start_dt = datetime.datetime.fromisoformat(start_time_str)
        end_dt = start_dt + datetime.timedelta(hours=1)
        end_time_str = end_dt.isoformat()

        # 4. Prepare Event Data
        event_data = {
            "summary": f"Meeting with {details.get('person_name', 'Unknown')}",
            "description": f"Original Request: {user_input}",
            "start_time": start_time_str,
            "end_time": end_time_str,
            "timezone": "Asia/Kolkata"
        }

        # 5. Authenticate & Create
        print("🔐 Authenticating with Google Calendar...")
        service = authenticate_google_calendar()
        
        print("🚀 Creating Event...")
        create_event(service, event_data)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

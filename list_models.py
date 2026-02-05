import requests
import json

API_KEY = "AIzaSyCfMOLzU9FAa0oH0p0UTAFPhdIUeiBrPZ4"

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(url)
    response.raise_for_status()

    models = response.json().get("models", [])
    
    with open("models.txt", "w", encoding="utf-8") as f:
        for m in models:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                f.write(f"{m['name']}\n")
    
    print(f"Successfully wrote {len(models)} models to models.txt")

except Exception as e:
    print(f"Error: {e}")

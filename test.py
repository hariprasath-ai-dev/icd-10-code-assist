import requests
import json

API_KEY = "AIzaSyDamoMlehAfBkD-vqRuAOxwQ4B54Dzu-ok"
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}

data = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Explain how AI works in a few words"
                }
            ]
        }
    ]
}

response = requests.post(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.json())
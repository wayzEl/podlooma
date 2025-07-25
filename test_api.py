import requests
import json

url = "http://localhost:8000/process-tts"

payload = {
    "dialogue": "Speaker 1: Hello! We're excited to show you our native speech capabilities\nSpeaker 2: Where you can direct a voice, create realistic dialog, and so much more. Edit these placeholders to get started.",
    "voices": {
        "Speaker 1": "Zephyr",
        "Speaker 2": "Puck"
    },
    "model": "gemini-2.5-flash-preview-tts",
    "api_key": "AIzaSyCJTbKMDAiojpqzvKbNakCiMDj_MEYOW6k",
    "webhook_url": "http://example.com/webhook",
    "Episode ID": "test_episode"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()  # Raise an exception for bad status codes
    print("Request successful!")
    print("Response JSON:", response.json())
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if e.response:
        print("Response status code:", e.response.status_code)
        print("Response text:", e.response.text)


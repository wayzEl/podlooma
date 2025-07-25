

import os
from dotenv import load_dotenv
import tasks_new

# Load environment variables from .env file
load_dotenv()

print("--- Starting Direct Task Execution ---")

# Manually define the arguments that would be passed to the task
task_kwargs = {
    "api_key": os.getenv("GOOGLE_API_KEY"),
    "model": "gemini-2.5-flash-preview-tts",
    "dialogue": "Speaker 1: This is a direct test of the task function.\nSpeaker 2: Let's see the output.",
    "voices": {
        "Speaker 1": "Zephyr",
        "Speaker 2": "Puck"
    },
    "webhook_url": "https://webhook.site/eb20dfb9-c5f7-437a-8e30-37cae9676f32",
    "episode_id": "debug_test_01",
    "base_url": "http://localhost:8000"
}

try:
    print("Attempting to call generate_tts_task...")
    result = tasks_new.generate_tts_task(**task_kwargs)
    print(f"--- Task Execution Successful ---")
    print(f"Result: {result}")

except Exception as e:
    import traceback
    print(f"--- Task Execution Failed ---")
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()



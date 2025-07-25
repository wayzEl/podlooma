import os
import base64
import wave
from google import genai
from google.genai import types
from rq import get_current_job
import requests
import traceback
import logging

# --- Detailed Logging Setup ---
log_file = "task_debug.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

IS_ON_RENDER = 'RENDER' in os.environ
AUDIO_DIR = "/data/audio" if IS_ON_RENDER else "output"

if not IS_ON_RENDER:
    os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_tts_task(api_key, model, dialogue, voices, webhook_url, episode_id, base_url):
    try:
        job = get_current_job()
        job_id = job.id if job else f"direct_{episode_id}"
        logging.info(f"--- Starting TTS Job: {job_id} ---")
        logging.info("1. Configuring Google AI Client...")
        client = genai.Client()
        logging.info("   - Client configured successfully.")

        logging.info("2. Building Speaker Configurations...")
        speaker_voice_configs = []
        for speaker_name, voice_name in voices.items():
            logging.info(f"   - Speaker: {speaker_name}, Voice: {voice_name}")
            speaker_voice_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=speaker_name,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                    )
                )
            )
        logging.info("   - Speaker configurations built.")

        logging.info("3. Building Generation Configuration...")
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(speaker_voice_configs=speaker_voice_configs)
            )
        )
        logging.info("   - Generation configuration built.")

        logging.info("4. Sending request to Google AI API...")
        response = client.models.generate_content(
            model=model,
            contents=[{"parts": [{"text": dialogue}]}],
            config=config
        )
        logging.info("   - API request sent.")
        
        logging.info(f"5. Analyzing API Response...")
        logging.info(f"   - Full Response Object: {response}")

        if not (response.candidates and response.candidates[0].content and response.candidates[0].content.parts and response.candidates[0].content.parts[0].inline_data and response.candidates[0].content.parts[0].inline_data.data):
            logging.error("   - CRITICAL: Audio data not found in the expected location in the response.")
            logging.error(f"   - Response Candidates: {response.candidates}")
            raise ValueError("Could not find audio data in the API response.")
        
        logging.info("   - Audio data found successfully.")

        logging.info("6. Processing Audio Data...")
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        logging.info(f"   - Raw audio data size: {len(audio_data)} bytes")

        # Save as WAV file using Google's documented method
        file_name = f"{job_id}.wav"
        file_path = os.path.join(AUDIO_DIR, file_name)
        
        # Use wave module as per Google docs
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)        # Mono
            wf.setsampwidth(2)        # 16-bit
            wf.setframerate(24000)    # 24kHz
            wf.writeframes(audio_data)
        
        logging.info(f"   - WAV file saved to: {file_path}")

        audio_url = f"{base_url}/audio/{file_name}"
        logging.info(f"   - Generated audio URL: {audio_url}")

        logging.info("7. Notifying Webhook...")
        webhook_payload = {"episode_id": episode_id, "status": "success", "audio_url": audio_url}
        requests.post(webhook_url, json=webhook_payload)
        logging.info("   - Webhook notified.")

        logging.info(f"--- Job {job_id} Completed Successfully ---")
        return audio_url

    except Exception as e:
        job_id = job_id if 'job_id' in locals() else f"unknown_{episode_id}"
        logging.error(f"--- Job {job_id} Failed ---")
        logging.error(f"Error: {e}")
        
        # Log the full traceback to the file
        with open("task_error.log", "a") as f:
            f.write(f"Job {job_id} failed.\n")
            f.write(f"Error: {e}\n")
            f.write("Traceback:\n")
            traceback.print_exc(file=f)
        
        logging.error("   - Full traceback logged to task_error.log")

        webhook_payload = {"episode_id": episode_id, "status": "failed", "error": str(e)}
        requests.post(webhook_url, json=webhook_payload)
        raise

import os
import base64
from pydub import AudioSegment
from google import genai
from google.genai import types
from rq import get_current_job
import requests

# The directory on the persistent disk where we will store audio files
AUDIO_DIR = "/data/audio"

def generate_tts_task(api_key, model, dialogue, voices, webhook_url, episode_id, base_url):
    """
    Generates the audio, saves it, and sends a notification to the webhook.
    """
    job = get_current_job()
    print(f"Starting job {job.id} for Episode {episode_id}...")

    try:
        client = genai.Client(api_key=api_key)

        speaker_voice_configs = []
        for speaker_name, voice_name in voices.items():
            speaker_voice_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=speaker_name,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    )
                )
            )

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_voice_configs
                )
            )
        )
        
        response = client.models.generate_content(
            model=model,
            contents=[{"parts": [{"text": dialogue}]}],
            config=config
        )

        if not (response.candidates and response.candidates[0].content.parts[0].inline_data.data):
            raise ValueError("Could not find audio data in the response.")

        audio_data_b64 = response.candidates[0].content.parts[0].inline_data.data
        audio_data_raw = base64.b64decode(audio_data_b64)

        audio_segment = AudioSegment(
            data=audio_data_raw,
            sample_width=2,
            frame_rate=24000,
            channels=1
        )
        
        file_name = f"{job.id}.mp3"
        file_path = os.path.join(AUDIO_DIR, file_name)
        audio_segment.export(file_path, format="mp3")
        
        # Construct the final public URL for the audio file
        audio_url = f"{base_url}/audio/{file_name}"
        
        print(f"Job {job.id} completed. Notifying webhook: {webhook_url}")

        # Send the success payload to the webhook
        webhook_payload = {
            "episode_id": episode_id,
            "status": "success",
            "audio_url": audio_url
        }
        requests.post(webhook_url, json=webhook_payload)
        
        return audio_url

    except Exception as e:
        print(f"Job {job.id} failed: {e}")
        # Send the failure payload to the webhook
        webhook_payload = {
            "episode_id": episode_id,
            "status": "failed",
            "error": str(e),
        }
        requests.post(webhook_url, json=webhook_payload)
        raise

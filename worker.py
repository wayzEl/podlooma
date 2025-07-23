import os
import base64
from pydub import AudioSegment
from google import genai
from google.genai import types
import redis
from rq import Worker, Queue, Connection

# The URL for the Redis instance provided by Render
listen = ['default']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

def generate_tts_task(api_key, model, dialogue, voices):
    """
    This is the actual long-running task that will be executed by the worker.
    """
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

        if response.candidates and response.candidates[0].content.parts[0].inline_data.data:
             audio_data_b64 = response.candidates[0].content.parts[0].inline_data.data
             audio_data_raw = base64.b64decode(audio_data_b64)
        else:
            raise ValueError("Could not find audio data in the response.")

        audio_segment = AudioSegment(
            data=audio_data_raw,
            sample_width=2,
            frame_rate=24000,
            channels=1
        )
        
        file_path = "output.mp3"
        audio_segment.export(file_path, format="mp3")
        
        print(f"Successfully generated audio and saved to {file_path}")
        return file_path

    except Exception as e:
        print(f"Task failed: {e}")
        raise

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()

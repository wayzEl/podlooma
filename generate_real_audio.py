#!/usr/bin/env python3
"""
Generate real TTS audio and receive webhook notification
"""
import requests
import json
import time
import os

# Configuration
TTS_API_URL = "http://localhost:8000"
WEBHOOK_SERVER_URL = "http://localhost:9000"
API_KEY = "AIzaSyDN8Uf0G0T0pJNzHgm5265zPoflCP_DjMs"

def generate_audio():
    """Generate real TTS audio"""
    
    print("🎵 GENERATING REAL TTS AUDIO")
    print("=" * 40)
    
    # Clear previous webhooks
    try:
        requests.delete(f"{WEBHOOK_SERVER_URL}/webhooks")
        print("✅ Cleared previous webhooks")
    except:
        pass
    
    # Submit TTS job
    dialogue = """Speaker 1: Hello! Welcome to our amazing TTS demonstration.
Speaker 2: This is so cool! The voices sound incredibly realistic.
Speaker 1: I know right? Google's Gemini AI does an amazing job with multi-speaker dialogue.
Speaker 2: And the webhook system means we get notified as soon as the audio is ready!"""
    
    job_payload = {
        "dialogue": dialogue,
        "voices": {
            "Speaker 1": "Zephyr",
            "Speaker 2": "Puck"
        },
        "model": "gemini-2.5-flash-preview-tts",
        "api_key": API_KEY,
        "webhook_url": f"{WEBHOOK_SERVER_URL}/webhook",
        "Episode ID": "real_audio_demo_001"
    }
    
    print(f"\n🚀 Submitting TTS job...")
    print(f"📝 Dialogue: {len(dialogue)} characters")
    print(f"🎭 Voices: Speaker 1 → Zephyr, Speaker 2 → Puck")
    
    try:
        response = requests.post(f"{TTS_API_URL}/process-tts", json=job_payload)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("job_id")
        
        print(f"✅ Job submitted successfully!")
        print(f"   Job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Failed to submit job: {e}")
        return None, None
    
    # Monitor job progress
    print(f"\n⏳ Processing audio (this may take 1-2 minutes)...")
    
    for i in range(30):  # Wait up to 5 minutes
        try:
            response = requests.get(f"{TTS_API_URL}/jobs/{job_id}")
            job_status = response.json()
            status = job_status.get("status")
            
            print(f"   Status: {status} ({i*10}s elapsed)")
            
            if status == "finished":
                print(f"🎉 Audio generation completed!")
                break
            elif status == "failed":
                print(f"❌ Job failed: {job_status.get('result', 'Unknown error')}")
                return job_id, None
                
            time.sleep(10)
            
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
            time.sleep(5)
    
    # Check webhook notification
    print(f"\n📬 Checking webhook notification...")
    try:
        response = requests.get(f"{WEBHOOK_SERVER_URL}/webhooks/latest")
        webhook_data = response.json()
        
        if "data" in webhook_data:
            data = webhook_data["data"]
            if data.get("status") == "success":
                audio_url = data.get("audio_url")
                print(f"✅ Webhook received!")
                print(f"🎵 Audio URL: {audio_url}")
                return job_id, audio_url
            else:
                print(f"❌ Webhook shows failure: {data.get('error')}")
        else:
            print(f"⚠️ No webhook received yet")
            
    except Exception as e:
        print(f"❌ Error checking webhook: {e}")
    
    return job_id, None

def download_and_play_audio(job_id, audio_url):
    """Download the audio file and provide instructions to play it"""
    
    if not audio_url:
        print("❌ No audio URL available")
        return
        
    print(f"\n💾 AUDIO FILE ACCESS")
    print("=" * 30)
    
    # Check if file exists locally
    local_file = f"output/{job_id}.mp3"
    if os.path.exists(local_file):
        print(f"✅ Audio file saved: {local_file}")
        print(f"📂 Full path: {os.path.abspath(local_file)}")
        
        # Get file size
        file_size = os.path.getsize(local_file)
        print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        print(f"\n🎧 TO LISTEN TO THE AUDIO:")
        print(f"   1. Direct download: {audio_url}")
        print(f"   2. Local file: open {os.path.abspath(local_file)}")
        print(f"   3. Terminal play: afplay {local_file}")
        
        # Try to play automatically on macOS
        try:
            import subprocess
            print(f"\n🔊 Attempting to play audio automatically...")
            subprocess.run(["afplay", local_file], check=True)
            print(f"✅ Audio playback completed!")
        except:
            print(f"⚠️ Auto-play failed. Please play manually using the methods above.")
    else:
        print(f"⚠️ Local file not found: {local_file}")
        print(f"📥 You can download from: {audio_url}")

if __name__ == "__main__":
    print("🎼 Real TTS Audio Generation")
    print("Make sure all services are running:")
    print("✓ Webhook server (port 9000)")
    print("✓ TTS API (port 8000)") 
    print("✓ Redis server")
    print("✓ Worker process")
    
    input("\nPress Enter to generate audio...")
    
    job_id, audio_url = generate_audio()
    
    if job_id:
        download_and_play_audio(job_id, audio_url)
    else:
        print("\n❌ Failed to generate audio") 
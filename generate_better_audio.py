#!/usr/bin/env python3
"""
Generate high-quality TTS audio with longer dialogue
"""
import requests
import json
import time
import os

# Configuration
TTS_API_URL = "http://localhost:8000"
WEBHOOK_SERVER_URL = "http://localhost:9000"
API_KEY = "AIzaSyDN8Uf0G0T0pJNzHgm5265zPoflCP_DjMs"

def generate_podcast_audio():
    """Generate a longer, more interesting TTS audio sample"""
    
    print("🎙️ GENERATING PODCAST-STYLE TTS AUDIO")
    print("=" * 50)
    
    # Clear previous webhooks
    try:
        requests.delete(f"{WEBHOOK_SERVER_URL}/webhooks")
        print("✅ Cleared previous webhooks")
    except:
        pass
    
    # Create longer, more interesting dialogue
    dialogue = """Dr. Sarah: Welcome back to Tech Talk Today! I'm Dr. Sarah Chen, and today we're diving deep into the fascinating world of artificial intelligence.

Alex: Thanks for having me on, Sarah! I'm Alex Rodriguez, and I'm absolutely thrilled to discuss how AI is revolutionizing everything from healthcare to entertainment.

Dr. Sarah: Alex, let's start with something our listeners are probably wondering about. How has text-to-speech technology evolved in the past few years?

Alex: Oh wow, it's been incredible! Just five years ago, synthetic voices sounded robotic and unnatural. Now, with models like Google's Gemini, we're getting voices that are practically indistinguishable from human speech.

Dr. Sarah: That's amazing! And what I find particularly exciting is the multi-speaker capability. We can now generate entire conversations, like this one, with different voices and personalities.

Alex: Exactly! And the applications are endless - audiobooks, podcast generation, voice assistants, accessibility tools. We're really entering a new era of human-computer interaction."""
    
    job_payload = {
        "dialogue": dialogue,
        "voices": {
            "Dr. Sarah": "Kore",      # Firm voice for the host
            "Alex": "Puck"            # Upbeat voice for the guest
        },
        "model": "gemini-2.5-flash-preview-tts",
        "api_key": API_KEY,
        "webhook_url": f"{WEBHOOK_SERVER_URL}/webhook",
        "Episode ID": "podcast_demo_001"
    }
    
    print(f"\n🚀 Submitting podcast TTS job...")
    print(f"📝 Dialogue: {len(dialogue)} characters")
    print(f"🎭 Voices: Dr. Sarah → Kore (Firm), Alex → Puck (Upbeat)")
    
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
    
    # Monitor job progress with more patience for longer audio
    print(f"\n⏳ Processing audio (longer dialogue may take 2-3 minutes)...")
    
    for i in range(40):  # Wait up to 6+ minutes for longer audio
        try:
            response = requests.get(f"{TTS_API_URL}/jobs/{job_id}")
            job_status = response.json()
            status = job_status.get("status")
            
            if i % 3 == 0:  # Print every 30 seconds
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

def play_and_analyze_audio(job_id, audio_url):
    """Play the audio and show file details"""
    
    if not audio_url:
        print("❌ No audio URL available")
        return
        
    print(f"\n🎧 AUDIO FILE ANALYSIS")
    print("=" * 35)
    
    # Check if file exists locally
    local_file = f"output/{job_id}.mp3"
    if os.path.exists(local_file):
        print(f"✅ Audio file saved: {local_file}")
        print(f"📂 Full path: {os.path.abspath(local_file)}")
        
        # Get file size
        file_size = os.path.getsize(local_file)
        print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # Estimate duration (rough calculation for MP3)
        estimated_duration = file_size / (128 * 1024 / 8)  # Assuming 128kbps
        print(f"⏱️ Estimated duration: ~{estimated_duration:.1f} seconds")
        
        print(f"\n🎧 WAYS TO LISTEN:")
        print(f"   1. Auto-play: Will attempt to play automatically")
        print(f"   2. Manual play: afplay {local_file}")
        print(f"   3. Open in app: open {local_file}")
        print(f"   4. Download: {audio_url}")
        
        # Try to play automatically on macOS
        try:
            import subprocess
            print(f"\n🔊 Playing audio automatically...")
            result = subprocess.run(["afplay", local_file], 
                                  check=True, 
                                  capture_output=True, 
                                  text=True,
                                  timeout=30)
            print(f"✅ Audio playback completed!")
        except subprocess.TimeoutExpired:
            print(f"⏰ Audio is still playing (longer than 30s)...")
        except Exception as e:
            print(f"⚠️ Auto-play failed: {e}")
            print(f"Please play manually using the methods above.")
    else:
        print(f"⚠️ Local file not found: {local_file}")
        print(f"📥 You can download from: {audio_url}")

if __name__ == "__main__":
    print("🎙️ High-Quality Podcast TTS Generation")
    print("Make sure all services are running:")
    print("✓ Webhook server (port 9000)")
    print("✓ TTS API (port 8000)") 
    print("✓ Redis server")
    print("✓ Worker process")
    
    input("\nPress Enter to generate podcast-style audio...")
    
    job_id, audio_url = generate_podcast_audio()
    
    if job_id:
        play_and_analyze_audio(job_id, audio_url)
    else:
        print("\n❌ Failed to generate audio")
        
    print(f"\n💡 TIP: If audio is short/empty, check:")
    print(f"   - Model name is correct: gemini-2.5-flash-preview-tts")
    print(f"   - API key has TTS permissions")
    print(f"   - Worker process is running without fork errors") 
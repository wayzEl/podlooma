import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
TTS_API_URL = "http://localhost:8000"
WEBHOOK_SERVER_URL = "http://localhost:9000"

def test_webhook_integration():
    """Test the complete webhook integration flow"""
    
    print("🧪 WEBHOOK INTEGRATION TEST")
    print("=" * 50)
    
    # Step 1: Clear any existing webhooks
    print("\n1️⃣ Clearing previous webhooks...")
    try:
        response = requests.delete(f"{WEBHOOK_SERVER_URL}/webhooks")
        print(f"✅ Cleared webhooks: {response.json()}")
    except Exception as e:
        print(f"⚠️ Could not clear webhooks: {e}")
    
    # Step 2: Submit TTS job with webhook
    print("\n2️⃣ Submitting TTS job...")
    
    job_payload = {
        "dialogue": "Speaker 1: Testing webhook functionality!\nSpeaker 2: This should trigger a callback when complete.",
        "voices": {
            "Speaker 1": "Zephyr",
            "Speaker 2": "Puck"
        },
        "model": "models/gemini-1.5-flash-preview-0514",
        "api_key": os.getenv("GOOGLE_API_KEY", "your-api-key-here"),
        "webhook_url": f"{WEBHOOK_SERVER_URL}/webhook",
        "Episode ID": "webhook_test_001"
    }
    
    try:
        response = requests.post(f"{TTS_API_URL}/process-tts", json=job_payload)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("job_id")
        
        print(f"✅ Job submitted successfully!")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {job_data.get('status')}")
        
    except Exception as e:
        print(f"❌ Failed to submit job: {e}")
        return False
    
    # Step 3: Monitor job status
    print(f"\n3️⃣ Monitoring job {job_id}...")
    max_wait = 300  # 5 minutes max
    wait_time = 0
    
    while wait_time < max_wait:
        try:
            response = requests.get(f"{TTS_API_URL}/jobs/{job_id}")
            job_status = response.json()
            status = job_status.get("status")
            
            print(f"   ⏳ Job status: {status} (waited {wait_time}s)")
            
            if status in ["finished", "failed"]:
                print(f"✅ Job completed with status: {status}")
                if status == "failed":
                    print(f"   Error: {job_status.get('result', 'Unknown error')}")
                break
                
            time.sleep(10)
            wait_time += 10
            
        except Exception as e:
            print(f"⚠️ Error checking job status: {e}")
            time.sleep(5)
            wait_time += 5
    
    if wait_time >= max_wait:
        print(f"⏰ Job did not complete within {max_wait} seconds")
    
    # Step 4: Check for webhook notifications
    print(f"\n4️⃣ Checking webhook notifications...")
    time.sleep(5)  # Give webhook a moment to arrive
    
    try:
        response = requests.get(f"{WEBHOOK_SERVER_URL}/webhooks")
        webhook_data = response.json()
        
        total_webhooks = webhook_data.get("total_webhooks", 0)
        print(f"📬 Total webhooks received: {total_webhooks}")
        
        if total_webhooks > 0:
            print("\n📄 Webhook Details:")
            for i, webhook in enumerate(webhook_data["webhooks"], 1):
                print(f"   Webhook #{i}:")
                print(f"     Timestamp: {webhook['timestamp']}")
                print(f"     Status: {webhook['data'].get('status')}")
                print(f"     Episode ID: {webhook['data'].get('episode_id')}")
                
                if webhook['data'].get('status') == 'success':
                    print(f"     Audio URL: {webhook['data'].get('audio_url')}")
                elif webhook['data'].get('status') == 'failed':
                    print(f"     Error: {webhook['data'].get('error')}")
                print()
            
            return True
        else:
            print("❌ No webhooks received!")
            return False
            
    except Exception as e:
        print(f"❌ Error checking webhooks: {e}")
        return False

def test_webhook_endpoints():
    """Test webhook server endpoints"""
    print("\n🔗 WEBHOOK SERVER ENDPOINT TEST")
    print("=" * 40)
    
    endpoints = [
        ("GET /", f"{WEBHOOK_SERVER_URL}/"),
        ("GET /webhooks", f"{WEBHOOK_SERVER_URL}/webhooks"),
        ("GET /webhooks/latest", f"{WEBHOOK_SERVER_URL}/webhooks/latest"),
    ]
    
    for name, url in endpoints:
        try:
            response = requests.get(url)
            print(f"✅ {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {e}")

if __name__ == "__main__":
    print("🔧 Starting Webhook Integration Tests...")
    print("\nMake sure both servers are running:")
    print("1. TTS API: python main.py (port 8000)")
    print("2. Worker: python worker.py")
    print("3. Webhook server: python webhook_test_server.py (port 9000)")
    
    input("\nPress Enter when both servers are ready...")
    
    # Test webhook server endpoints first
    test_webhook_endpoints()
    
    # Run full integration test
    success = test_webhook_integration()
    
    if success:
        print("\n🎉 WEBHOOK INTEGRATION TEST PASSED!")
    else:
        print("\n❌ WEBHOOK INTEGRATION TEST FAILED!") 
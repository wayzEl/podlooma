#!/usr/bin/env python3
"""
Quick webhook test - sends a test payload directly to verify webhook processing
"""
import requests
import json

def test_webhook_endpoint():
    """Test webhook endpoint with sample data"""
    webhook_url = "http://localhost:9000/webhook"
    
    # Sample webhook payloads that your TTS service would send
    success_payload = {
        "episode_id": "test_episode_001",
        "status": "success", 
        "audio_url": "http://localhost:8000/audio/test_job_123.mp3"
    }
    
    failure_payload = {
        "episode_id": "test_episode_002", 
        "status": "failed",
        "error": "API key invalid"
    }
    
    print("🧪 QUICK WEBHOOK TEST")
    print("=" * 30)
    
    # Test success webhook
    print("\n✅ Testing SUCCESS webhook...")
    try:
        response = requests.post(webhook_url, json=success_payload)
        print(f"   Response: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test failure webhook  
    print("\n❌ Testing FAILURE webhook...")
    try:
        response = requests.post(webhook_url, json=failure_payload)
        print(f"   Response: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check received webhooks
    print("\n📋 Checking received webhooks...")
    try:
        response = requests.get("http://localhost:9000/webhooks")
        data = response.json()
        print(f"   Total webhooks: {data['total_webhooks']}")
        
        for webhook in data['webhooks']:
            print(f"   - {webhook['data']['status']}: {webhook['data']['episode_id']}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("Make sure webhook server is running: python webhook_test_server.py")
    input("Press Enter to continue...")
    test_webhook_endpoint() 
from fastapi import FastAPI, Request
import uvicorn
import json
from datetime import datetime

app = FastAPI()

# Store received webhooks for testing
received_webhooks = []

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive webhook notifications from the TTS service"""
    try:
        # Get the raw body and JSON data
        body = await request.body()
        data = await request.json()
        
        # Create webhook entry with timestamp
        webhook_entry = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "raw_body": body.decode('utf-8'),
            "headers": dict(request.headers)
        }
        
        received_webhooks.append(webhook_entry)
        
        print(f"\n🔔 WEBHOOK RECEIVED at {webhook_entry['timestamp']}")
        print(f"📄 Data: {json.dumps(data, indent=2)}")
        
        return {"status": "webhook received", "message": "Success"}
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/webhooks")
def get_received_webhooks():
    """View all received webhooks"""
    return {
        "total_webhooks": len(received_webhooks),
        "webhooks": received_webhooks
    }

@app.get("/webhooks/latest")
def get_latest_webhook():
    """Get the most recent webhook"""
    if received_webhooks:
        return received_webhooks[-1]
    return {"message": "No webhooks received yet"}

@app.delete("/webhooks")
def clear_webhooks():
    """Clear all received webhooks"""
    global received_webhooks
    count = len(received_webhooks)
    received_webhooks = []
    return {"message": f"Cleared {count} webhooks"}

@app.get("/")
def root():
    return {
        "message": "Webhook Test Server Running",
        "endpoints": {
            "receive_webhook": "POST /webhook",
            "view_all": "GET /webhooks", 
            "view_latest": "GET /webhooks/latest",
            "clear_all": "DELETE /webhooks"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Webhook Test Server on http://localhost:9000")
    print("📬 Webhook endpoint: http://localhost:9000/webhook")
    print("👀 View webhooks at: http://localhost:9000/webhooks")
    uvicorn.run(app, host="0.0.0.0", port=9000) 
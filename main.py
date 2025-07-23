from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from rq import Queue
from rq.job import Job
from redis import from_url as redis_from_url
import os
from worker import generate_tts_task

# --- App and Queue Setup ---
app = FastAPI()

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis_from_url(redis_url)
q = Queue(connection=conn)

AUDIO_DIR = "/data/audio"

# --- FastAPI Endpoints ---
@app.get("/")
def read_root():
    return {"message": "TTS API with webhooks is running."}

@app.post("/process-tts/")
async def queue_tts_job(request: Request):
    data = await request.json()
    
    dialogue = data.get("dialogue")
    voices = data.get("voices")
    model = data.get("model")
    api_key = data.get("api_key")
    webhook_url = data.get("webhook_url")
    episode_id = data.get("Episode ID")

    if not all([dialogue, voices, model, api_key, webhook_url, episode_id]):
        raise HTTPException(status_code=400, detail="Missing required fields.")

    base_url = os.getenv("RENDER_EXTERNAL_URL", f"https://{request.headers['host']}")

    job = q.enqueue(
        generate_tts_task,
        kwargs={
            "api_key": api_key,
            "model": model,
            "dialogue": dialogue,
            "voices": voices,
            "webhook_url": webhook_url,
            "episode_id": episode_id,
            "base_url": base_url,
        },
        job_timeout='15m'
    )

    return {"status": "queued", "job_id": job.get_id()}

@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=conn)
    except Exception:
        return {"error": "Job not found"}

    return {
        "job_id": job.id,
        "status": job.get_status(),
        "result": job.result,
    }

@app.get("/audio/{job_id}.mp3")
def download_audio(job_id: str):
    file_path = os.path.join(AUDIO_DIR, f"{job_id}.mp3")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='audio/mpeg', filename=f"{job_id}.mp3")
    else:
        raise HTTPException(status_code=404, detail="File not found.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
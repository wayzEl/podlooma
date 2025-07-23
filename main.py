from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from rq import Queue, Worker
from rq.job import Job
from redis import from_url as redis_from_url
import os
import threading
import time
from redis import from_url as redis_from_url
from rq import Queue, Worker
from worker import generate_tts_task

# --- App and Queue Setup ---
app = FastAPI()

# The main connection for the web process to enqueue jobs
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis_from_url(redis_url)
q = Queue(connection=conn)

# The directory on the persistent disk where audio files are stored
AUDIO_DIR = "/data/audio"

# --- Worker Function ---
def run_worker():
    """
    This function runs in a background thread and processes jobs from the queue.
    """
    listen = ['default']
    worker_conn = redis_from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
    worker = Worker(listen, connection=worker_conn)

    # Run the worker in a loop with burst mode.
    # This prevents it from installing signal handlers, avoiding the error.
    while True:
        try:
            worker.work(burst=True)
        except Exception as e:
            print(f"Worker error: {e}")
        # Sleep for a short duration to prevent a tight loop from consuming CPU
        time.sleep(1)


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
        raise HTTPException(status_code=400, detail="Missing required fields, including webhook_url and Episode ID.")

    # The base URL of our service, needed to construct the download URL.
    # Render provides the RENDER_EXTERNAL_URL environment variable.
    base_url = os.getenv("RENDER_EXTERNAL_URL", f"http://{request.client.host}")

    job = q.enqueue(
        generate_tts_task,
        api_key=api_key,
        model=model,
        dialogue=dialogue,
        voices=voices,
        webhook_url=webhook_url,
        episode_id=episode_id,
        base_url=base_url,
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
        return {"error": "File not found. The job may still be processing or has failed."}, 404

# --- Application Startup ---
@app.on_event("startup")
def start_worker_thread():
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    print("Starting background RQ worker thread...")

if __name__ == "__main__":
    import uvicorn
    start_worker_thread()
    uvicorn.run(app, host="0.0.0.0", port=8000)

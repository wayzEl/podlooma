from fastapi import FastAPI, Request, HTTPException
from rq import Queue
from redis import from_url as redis_from_url
import os
import threading
from worker import generate_tts_task # Import the task function directly

# --- App and Queue Setup ---
app = FastAPI()

# Connect to the Redis instance provided by Render
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis_from_url(redis_url)
q = Queue(connection=conn)

# --- Worker Function ---
# This function will run in a background thread
def run_worker():
    listen = ['default']
    # The 'worker.py' file still contains the task function, so we need to be able to import it.
    # We ensure the connection is established within the thread.
    with Connection(redis_from_url(redis_url)):
        # Create a worker that listens to the 'default' queue
        worker = Worker(map(Queue, listen))
        # The work() method is blocking, so it will run forever in this thread
        print("Background worker started and listening for jobs...")
        worker.work()

# --- FastAPI Endpoints ---
@app.get("/")
def read_root():
    return {"message": "TTS API is running. Use the /process-tts/ endpoint to queue a job."}

@app.post("/process-tts/")
def queue_tts_job(request: Request):
    """
    Accepts a request, and enqueues the TTS generation task.
    """
    data = request.json()
    
    dialogue = data.get("dialogue")
    voices = data.get("voices")
    model = data.get("model")
    api_key = data.get("api_key")

    if not all([dialogue, voices, model, api_key]):
        raise HTTPException(status_code=400, detail="Missing required fields.")

    # Enqueue the job. The 'generate_tts_task' function from worker.py will be called.
    # The worker is running in the background thread of this same process.
    job = q.enqueue(
        'worker.generate_tts_task', # The path to the function in worker.py
        api_key,
        model,
        dialogue,
        voices,
        job_timeout='15m' # Set a generous timeout for the job
    )

    return {"status": "queued", "job_id": job.get_id()}

# --- Application Startup ---
@app.on_event("startup")
def start_worker_thread():
    """
    This function is called when the FastAPI application starts up.
    It creates and starts the background thread for our RQ worker.
    """
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    print("Starting background RQ worker thread...")

if __name__ == "__main__":
    import uvicorn
    # This part is for local testing and won't be used by Render's startCommand
    start_worker_thread()
    uvicorn.run(app, host="0.0.0.0", port=8000)

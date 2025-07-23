from fastapi import FastAPI, Request, HTTPException
from rq import Queue
import redis
import os

app = FastAPI()

# Connect to the Redis instance
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)
q = Queue(connection=conn)

# The endpoint that receives the request and queues the job
@app.post("/process-tts/")
def queue_tts_job(request: Request):
    data = request.json()
    
    dialogue = data.get("dialogue")
    voices = data.get("voices")
    model = data.get("model")
    api_key = data.get("api_key")

    if not all([dialogue, voices, model, api_key]):
        raise HTTPException(status_code=400, detail="Missing required fields.")

    # Enqueue the job. The 'generate_tts_task' function from worker.py will be called.
    job = q.enqueue(
        'worker.generate_tts_task', # The path to the function
        api_key,
        model,
        dialogue,
        voices,
        job_timeout='10m' # Set a long timeout for the job itself
    )

    return {"status": "queued", "job_id": job.get_id()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
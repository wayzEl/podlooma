import os
from redis import from_url
from rq import Worker, Queue
import traceback
import tasks_new  # Explicitly import the tasks module
from dotenv import load_dotenv

load_dotenv()

listen = ['default']

if __name__ == '__main__':
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        conn = from_url(redis_url)
        
        # This is the standard way to start a worker
        worker = Worker(list(map(lambda name: Queue(name, connection=conn), listen)), connection=conn)
        
        print("Worker starting successfully...")
        worker.work()

    except Exception as e:
        # If the worker fails to even start, log the error to a file.
        with open("worker_startup_error.log", "w") as f:
            f.write("Worker failed to start.\n")
            f.write(f"Error: {e}\n")
            f.write("Traceback:\n")
            traceback.print_exc(file=f)
        print(f"Worker failed to start. See worker_startup_error.log for details.")
        raise


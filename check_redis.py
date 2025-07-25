import os
from redis import from_url
from rq import Queue

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = from_url(redis_url)
q = Queue('default', connection=conn)

print(f"Number of jobs in 'default' queue: {len(q.jobs)}")
if len(q.jobs) > 0:
    print("Jobs are waiting in the queue.")
    print("This means the main application is working correctly, but the worker is not processing them.")
else:
    print("There are no jobs in the queue.")
import os

# --- Environment Setup ---
IS_ON_RENDER = "RENDER" in os.environ
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# --- Directory and File Paths ---
AUDIO_DIR = "/data/audio" if IS_ON_RENDER else "output"
LOG_DIR = "/var/log" if IS_ON_RENDER else "logs"
TASK_LOG_FILE = os.path.join(LOG_DIR, "task_debug.log")
TASK_ERROR_LOG_FILE = os.path.join(LOG_DIR, "task_error.log")
WORKER_STARTUP_ERROR_LOG_FILE = os.path.join(LOG_DIR, "worker_startup_error.log")


# --- Queue Configuration ---
DEFAULT_QUEUE_NAME = "default"

# --- Create directories if not on Render ---
if not IS_ON_RENDER:
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, File, UploadFile
from celery import Celery
from celery.result import AsyncResult
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
# Use redis://redis:6379/0 if running in docker, otherwise redis://localhost:6379/0
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

app = FastAPI(
    title="Multi-Agent Code Review API",
    description="An API for triggering and monitoring a multi-agent code review process.",
    version="1.0.0"
)

@app.post("/review", status_code=202)
async def submit_review(file: UploadFile = File(...)):
    """
    Accepts a zip file of the repository, submits it for review, and returns a task ID.
    """
    logger.info(f"Received review request for file: {file.filename}")
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .zip file.")

    contents = await file.read()
    task = celery_app.send_task("worker.run_review_agent", args=[contents])
    logger.info(f"Task {task.id} sent to worker.")
    return {"task_id": task.id}


@app.get("/results/{task_id}")
def get_review_result(task_id: str):
    """
    Retrieves the result of a review task using its task ID.
    """
    logger.info(f"Fetching result for task {task_id}.")
    task_result = AsyncResult(task_id, app=celery_app)

    if not task_result.ready():
        logger.info(f"Task {task_id} is not ready. Current state: {task_result.state}")
        return {"status": task_result.state, "result": None}

    if task_result.failed():
        logger.error(f"Task {task_id} failed.", exc_info=task_result.info)
        raise HTTPException(status_code=500, detail=str(task_result.info))

    result = task_result.get()
    logger.info(f"Task {task_id} completed successfully.")
    return {"status": task_result.state, "result": result}


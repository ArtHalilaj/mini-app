from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from tasks import compute_job

app = FastAPI(
    title="Distributed Compute Demo",
    description="FastAPI + Celery + Redis demo for parallel background computation.",
    version="1.0.0",
)

# Allow the frontend (running on a different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/jobs", summary="Submit a new computation job")
def submit_job(n: int = 10):
    """
    Kick off a background job split into **n** parallel Celery tasks.

    - **n**: number of parallel chunks (1–50)

    Returns a `job_id` you can poll with `GET /jobs/{job_id}`.
    """
    if n < 1 or n > 50:
        raise HTTPException(status_code=400, detail="n must be between 1 and 50")

    task = compute_job.delay(n)
    return {"job_id": task.id, "status": "submitted", "chunks": n}


@app.get("/jobs/{job_id}", summary="Poll job status and result")
def get_job_status(job_id: str):
    """
    Check the status of a previously submitted job.

    Possible status values: **PENDING**, **STARTED**, **SUCCESS**, **FAILURE**

    The `result` field is populated once status is **SUCCESS**.
    """
    result = AsyncResult(job_id)
    return {
        "job_id": job_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }

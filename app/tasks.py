import os
import time
from celery import Celery, group

BROKER_URL     = os.getenv("CELERY_BROKER_URL",    "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)


@celery_app.task
def compute_chunk(start: int, end: int) -> int:
    """
    Simulate CPU-bound work on a slice of integers.
    The sleep represents actual processing time in a real app.
    """
    time.sleep(1)
    return sum(range(start, end))


@celery_app.task
def compute_job(n: int) -> dict:
    """
    Split the total computation into n independent chunks using a Celery group.
    All chunks are dispatched in parallel and results aggregated when done.
    """
    total_numbers = 1000
    chunk_size    = total_numbers // n

    job_group = group(
        compute_chunk.s(i * chunk_size, (i + 1) * chunk_size)
        for i in range(n)
    )

    group_result = job_group.apply_async()
    values = group_result.get(timeout=60, disable_sync_subtasks=False)

    return {
        "chunks":     n,
        "chunk_size": chunk_size,
        "total":      sum(values),
    }

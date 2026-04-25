# Distributed Compute Demo

A mini full-stack app demonstrating distributed background processing with **FastAPI**, **Celery**, **Redis**, and a plain HTML/JS frontend - all wired together with **Docker Compose**.

## What it does

You submit a computation job from the browser by choosing how many parallel chunks to split it into. The FastAPI backend dispatches the job to a Celery worker via Redis, the worker runs the chunks in parallel, and the frontend polls until the result is ready and displays it.

It's a practical demo of the producer → broker → worker → result pattern that underpins real-world task queues (email sending, image processing, data pipelines, etc.).

---

## Architecture

```
Browser (port 3000)
    │
    ▼
Frontend — Nginx serving index.html
    │  POST /jobs?n=...
    │  GET  /jobs/{job_id}
    ▼
API — FastAPI (port 8000)
    │  dispatches Celery task
    ▼
Redis (port 6379) ◄──── message broker & result backend
    │
    ▼
Worker — Celery (4 concurrent workers)
    └── compute_chunk tasks run in parallel, results aggregated
```

### Services (docker-compose)

| Service    | Image / Build     | Port  | Role                              |
|------------|-------------------|-------|-----------------------------------|
| `redis`    | redis:7-alpine    | 6379  | Message broker & result backend   |
| `api`      | ./app             | 8000  | FastAPI HTTP server               |
| `worker`   | ./app             | —     | Celery worker (concurrency = 4)   |
| `frontend` | ./frontend        | 3000  | Nginx serving the HTML UI         |

---

## Project structure

```
mini-app/
├── app/
│   ├── main.py           # FastAPI app — POST /jobs, GET /jobs/{id}
│   ├── tasks.py          # Celery app — compute_chunk & compute_job tasks
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # python:3.12-slim image
├── frontend/
│   ├── index.html        # Single-page UI (vanilla HTML/CSS/JS)
│   └── Dockerfile        # nginx:alpine serving the HTML
├── docker-compose.yml    # Orchestrates all four services
├── .gitignore
└── README.md
```

---

## Getting started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) installed

### Run the app

```bash
git clone https://github.com/ArtHalilaj/mini-app.git
cd mini-app
docker compose up --build
```

Once all containers are up:

| URL                        | What you'll find          |
|----------------------------|---------------------------|
| http://localhost:3000      | The frontend UI           |
| http://localhost:8000/docs | FastAPI interactive docs  |

### Stop the app

```bash
docker compose down
```

---

## API reference

### `POST /jobs?n={n}`

Submits a new computation job split into `n` parallel chunks.

**Query param:** `n` - number of chunks, integer between 1 and 50.

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "submitted",
  "chunks": 5
}
```

---

### `GET /jobs/{job_id}`

Polls the status of a previously submitted job.

**Possible status values:** `PENDING` · `STARTED` · `SUCCESS` · `FAILURE`

**Response (while running):**
```json
{
  "job_id": "abc123...",
  "status": "PENDING",
  "result": null
}
```

**Response (on success):**
```json
{
  "job_id": "abc123...",
  "status": "SUCCESS",
  "result": {
    "chunks": 5,
    "chunk_size": 200,
    "total": 499500
  }
}
```

---

## How the task queue works

1. `POST /jobs` calls `compute_job.delay(n)` - this serialises the task and pushes it onto the Redis queue.
2. The Celery worker picks it up, builds a `group` of `n` independent `compute_chunk` subtasks, and dispatches them all in parallel.
3. Each `compute_chunk(start, end)` sleeps for 1 second (simulating CPU work) and returns the sum of integers in its range.
4. Once all chunks finish, `compute_job` aggregates the results and stores the final dict in Redis.
5. The frontend polls `GET /jobs/{job_id}` every second until status is `SUCCESS` or `FAILURE`.

---

## Dependencies

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
celery==5.3.6
redis==5.0.4
```

---

## Notes

- `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are passed as environment variables in `docker-compose.yml`, so you can swap Redis for RabbitMQ or another broker without touching the code.
- Worker concurrency is set to 4 (`--concurrency=4`). Increase it for heavier workloads.

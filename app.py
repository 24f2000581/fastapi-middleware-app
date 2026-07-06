from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import time
import uuid
from collections import defaultdict, deque
import os

app = FastAPI()

# =========================
# CONFIG
# =========================

EMAIL = os.getenv("EMAIL", "your_email@example.com")

ALLOWED_ORIGIN = "https://app-kb6lf9.example.com"

RATE_LIMIT = 8
WINDOW = 10

client_store = defaultdict(deque)

# =========================
# CORS (DO THIS FIRST)
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# RATE LIMIT MIDDLEWARE
# =========================

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    window_start = now - WINDOW

    q = client_store[client_id]

    while q and q[0] < window_start:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"error": "rate limit exceeded"}
        )

    q.append(now)

    response = await call_next(request)
    return response


# =========================
# REQUEST ID MIDDLEWARE
# =========================

@app.middleware("http")
async def request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response


# =========================
# ENDPOINTS
# =========================

@app.get("/ping")
@app.get("/ping/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }


# OPTIONAL: explicit OPTIONS safety (prevents 405 issues)
@app.options("/ping")
@app.options("/ping/ping")
async def options_handler():
    return JSONResponse(content={"ok": True})

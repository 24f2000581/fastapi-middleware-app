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

RATE_LIMIT = 8   # B requests
WINDOW = 10      # seconds

# =========================
# STORAGE
# =========================

client_store = defaultdict(deque)

# =========================
# CORS (STRICT)
# =========================

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)

    origin = request.headers.get("origin")

    # Only allow assigned origin
    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN

    return response


# =========================
# REQUEST CONTEXT MIDDLEWARE
# =========================

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response


# =========================
# RATE LIMIT MIDDLEWARE
# =========================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    window_start = now - WINDOW

    q = client_store[client_id]

    # remove old requests
    while q and q[0] < window_start:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"error": "rate limit exceeded"}
        )

    q.append(now)

    return await call_next(request)


# =========================
# ENDPOINT
# =========================

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
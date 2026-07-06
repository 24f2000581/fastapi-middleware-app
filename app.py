from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uuid
import time
from collections import defaultdict, deque
import os

app = FastAPI()

EMAIL = "24f2000581@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-kb6lf9.example.com"

RATE_LIMIT = 8
WINDOW = 10

client_store = defaultdict(deque)

# =========================
# ONLY CORS (NO CUSTOM CORS)
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
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    window_start = now - WINDOW

    q = client_store[client_id]

    while q and q[0] < window_start:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"error": "rate limit exceeded"})

    q.append(now)

    return await call_next(request)

# =========================
# REQUEST ID MIDDLEWARE
# =========================

@app.middleware("http")
async def request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response

# =========================
# ENDPOINT
# =========================

@app.get("/ping")
async def ping(request: Request):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    return {
        "email": EMAIL,
        "request_id": request_id
    }

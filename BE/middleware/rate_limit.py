from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict, deque

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static files and health checks
        if request.url.path in ["/health", "/"] or request.url.path.startswith("/static"):
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host
        current_time = time.time()

        # Clean old requests
        client_requests = self.clients[client_ip]
        while client_requests and client_requests[0] <= current_time - self.period:
            client_requests.popleft()

        # Check rate limit
        if len(client_requests) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )

        # Add current request
        client_requests.append(current_time)

        response = await call_next(request)
        return response
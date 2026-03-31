"""Security middleware for the CLM Platform."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared instance of Rate Limiter for the whole app
limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict transport security (HTTPS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Content Security Policy (relaxed for API + SPA)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:* ws://localhost:*"
        )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests for security monitoring."""

    async def dispatch(self, request: Request, call_next) -> Response:
        import time
        import uuid

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        # Calculate duration
        duration = round((time.time() - start_time) * 1000, 2)

        # Log request (structured)
        client_ip = request.client.host if request.client else "unknown"
        print(
            f"[{correlation_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration}ms) "
            f"IP={client_ip}"
        )

        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id

        return response

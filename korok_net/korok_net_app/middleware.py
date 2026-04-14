from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone


class SimpleRateLimitMiddleware:
    """Basic per-IP throttling for auth-heavy and public endpoints."""

    auth_paths = {
        "/authorization/",
        "/registration/",
        "/admin-login/",
        "/check-username/",
        "/check-email/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip = self.get_client_ip(request)
        request_path = request.path.rstrip("/") + "/" if request.path != "/" else "/"
        is_auth_path = request_path in self.auth_paths or any(
            request_path.endswith(path) for path in self.auth_paths if path != "/"
        )

        if is_auth_path:
            limited_response = self.check_limit(
                key=f"rate:auth:{client_ip}",
                limit=15,
                window_seconds=60,
                message="Слишком много запросов за короткое время. Повторите попытку позже.",
            )
            if limited_response:
                return limited_response
        else:
            limited_response = self.check_limit(
                key=f"rate:global:{client_ip}",
                limit=240,
                window_seconds=60,
                message="Превышен допустимый объём запросов. Повторите попытку позже.",
            )
            if limited_response:
                return limited_response

        response = self.get_response(request)
        response["X-RateLimit-Checked-At"] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        return response

    @staticmethod
    def get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    @staticmethod
    def check_limit(key, limit, window_seconds, message):
        current = cache.get(key, 0)
        if current >= limit:
            return HttpResponse(message, status=429)
        cache.set(key, current + 1, timeout=window_seconds)
        return None


class ContentSecurityPolicyMiddleware:
    """Adds a restrictive CSP to reduce XSS attack surface."""

    policy = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "upgrade-insecure-requests"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = self.policy
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

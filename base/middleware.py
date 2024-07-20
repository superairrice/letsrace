# project/middleware.py
import re
from django.http import HttpResponseForbidden


class BlockIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.blocked_ip_pattern = re.compile(r"^192\.168\.1\.\d{1,3}$")

    def __call__(self, request):
        ip = self.get_client_ip(request)
        if self.is_blocked_ip(ip):
            return HttpResponseForbidden("Forbidden: Access is denied.")

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def is_blocked_ip(self, ip):
        return self.blocked_ip_pattern.match(ip) is not None

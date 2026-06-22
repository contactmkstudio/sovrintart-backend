from django.http import JsonResponse
from functools import wraps
import json

ADMIN_EMAILS = [
    "vhnagarajrakesh@gmail.com",
    "contact.mkstudio@protonmail.com",
]


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        # Try to get email from header first
        user_email = request.headers.get('X-User-Email', '').strip().lower()

        # If not in header, try request body
        if not user_email:
            try:
                body = json.loads(request.body)
                user_email = body.get('user_email', '').strip().lower()
            except (json.JSONDecodeError, Exception):
                pass

        # If not in body, try query params
        if not user_email:
            user_email = request.GET.get('user_email', '').strip().lower()

        if user_email not in ADMIN_EMAILS:
            return JsonResponse({"error": "Not authorized"}, status=403)
        return view_func(self, request, *args, **kwargs)
    return wrapper

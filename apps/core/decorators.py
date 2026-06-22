from django.http import JsonResponse
from functools import wraps

ADMIN_EMAILS = [
    "vhnagarajrakesh@gmail.com",
    "contact.mkstudio@protonmail.com",
]


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user_email = request.headers.get('X-User-Email', '').strip().lower()
        if user_email not in ADMIN_EMAILS:
            return JsonResponse({"error": "Not authorized"}, status=403)
        return view_func(self, request, *args, **kwargs)
    return wrapper

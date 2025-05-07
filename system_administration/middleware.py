import threading

_user = threading.local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user.username if request.user.is_authenticated else None
        response = self.get_response(request)
        return response

def get_current_user():
    return getattr(_user, 'value', None)
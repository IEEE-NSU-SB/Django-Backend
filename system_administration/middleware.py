import threading

_request  = threading.local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            _request.user = request.user.username if request.user.is_authenticated else None
            _request.request = request
            response = self.get_response(request)
            return response
        except:
            # Ignore and forward the response
            response = self.get_response(request)
            return response
        finally:
            _request.user = None  # Clean up after the request is done
            _request.request = None

def get_current_user():
    return getattr(_request, 'user', None)

def get_current_request():
    return getattr(_request, 'request', None)

def get_client_ip():
    request = get_current_request()
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')
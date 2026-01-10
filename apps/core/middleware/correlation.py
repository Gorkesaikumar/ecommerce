import uuid
import threading

_request_local = threading.local()

class CorrelationIDMiddleware:
    """
    Injects X-Request-ID into all requests and responses.
    Stores it in thread-local storage for access in logging.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get or generate correlation ID
        correlation_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        
        # Store in thread-local for logger access
        _request_local.correlation_id = correlation_id
        
        # Add to request for easy access
        request.correlation_id = correlation_id
        
        response = self.get_response(request)
        
        # Add to response headers
        response['X-Request-ID'] = correlation_id
        
        return response

def get_correlation_id():
    """Utility to retrieve correlation ID from anywhere in request cycle"""
    return getattr(_request_local, 'correlation_id', None)

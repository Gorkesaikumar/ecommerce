from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
import logging

logger = logging.getLogger('api_errors')

def custom_exception_handler(exc, context):
    """
    Centralized exception handler with:
    - Sanitized error responses (no stack traces)
    - Consistent error structure
    - Correlation ID injection
    - Error logging
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)
    
    request = context.get('request')
    correlation_id = getattr(request, 'correlation_id', None) if request else None
    
    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        response = Response({
            'error': 'Validation Error',
            'details': exc.messages if hasattr(exc, 'messages') else str(exc),
            'correlation_id': correlation_id
        }, status=400)
    
    # If not handled by DRF
    if response is None:
        if isinstance(exc, Http404):
            response = Response({
                'error': 'Not Found',
                'correlation_id': correlation_id
            }, status=404)
        else:
            # Unexpected error
            logger.error(
                f"Unhandled exception: {exc}",
                extra={'correlation_id': correlation_id},
                exc_info=True
            )
            response = Response({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Please contact support.',
                'correlation_id': correlation_id
            }, status=500)
    else:
        # Add correlation ID to existing DRF error response
        if correlation_id and isinstance(response.data, dict):
            response.data['correlation_id'] = correlation_id
    
    # Log all errors
    logger.error(
        f"API Error: {exc.__class__.__name__}",
        extra={
            'correlation_id': correlation_id,
            'status_code': response.status_code,
            'path': request.path if request else None,
            'method': request.method if request else None,
        }
    )
    
    return response

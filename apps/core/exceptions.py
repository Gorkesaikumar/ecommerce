from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.conf import settings
import logging

logger = logging.getLogger('api_errors')

from django.db import IntegrityError

def custom_exception_handler(exc, context):
    """
    Centralized exception handler with:
    - Sanitized error responses (no stack traces)
    - Consistent error structure
    - Correlation ID injection
    - Error logging
    - Handling for Database Integrity Errors (409 Conflict)
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
    
    # Handle Database Integrity Errors (Uniqueness conflicts)
    if isinstance(exc, IntegrityError):
        response = Response({
            'error': 'Conflict',
            'message': 'This resource already exists. Please check your data.',
            'detail': str(exc) if settings.DEBUG else 'Data integrity violation.',
            'correlation_id': correlation_id
        }, status=409)

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
    if response:
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

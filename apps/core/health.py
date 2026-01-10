from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache

class HealthCheckView(APIView):
    """
    Health check endpoint for load balancers and monitoring
    Returns 200 if all systems operational
    """
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Check database
        try:
            connection.ensure_connection()
            health_status['checks']['database'] = 'ok'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = f'error: {str(e)}'
        
        # Check Redis
        try:
            cache.set('health_check', 'ok', timeout=10)
            cache_result = cache.get('health_check')
            if cache_result == 'ok':
                health_status['checks']['redis'] = 'ok'
            else:
                health_status['checks']['redis'] = 'error: unexpected value'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['redis'] = f'error: {str(e)}'
        
        # Return appropriate status code
        if health_status['status'] == 'unhealthy':
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(health_status, status=status.HTTP_200_OK)

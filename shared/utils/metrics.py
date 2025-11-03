from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time

class ServiceMetrics:
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Service info
        self.service_info = Info(
            f'{service_name}_info',
            'Service information'
        )
        
        # Request metrics
        self.requests_total = Counter(
            f'{service_name}_requests_total',
            'Total requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            f'{service_name}_request_duration_seconds',
            'Request duration',
            ['method', 'endpoint']
        )
        
        # Business metrics
        self.operations_total = Counter(
            f'{service_name}_operations_total',
            'Total operations',
            ['operation', 'status']
        )
        
        self.active_operations = Gauge(
            f'{service_name}_active_operations',
            'Active operations'
        )
    
    def track_request(self, method: str, endpoint: str):
        """Decorator to track request metrics"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    raise
                finally:
                    duration = time.time() - start_time
                    self.requests_total.labels(
                        method=method,
                        endpoint=endpoint,
                        status=status
                    ).inc()
                    self.request_duration.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(duration)
            
            return wrapper
        return decorator
from celery import Celery
from kombu import Queue, Exchange

def create_optimized_celery(broker_url: str, backend_url: str):
    """Create optimized Celery instance"""
    
    app = Celery('opscraft')
    
    app.conf.update(
        broker_url=broker_url,
        result_backend=backend_url,
        
        # Optimization settings
        task_serializer='pickle',
        result_serializer='pickle',
        accept_content=['pickle', 'json'],
        timezone='UTC',
        enable_utc=True,
        
        # Performance tuning
        worker_prefetch_multiplier=4,
        worker_max_tasks_per_child=1000,
        worker_disable_rate_limits=True,
        
        # Result backend optimization
        result_expires=3600,
        result_compression='gzip',
        
        # Task routing
        task_routes={
            'execute_script': {'queue': 'execution', 'priority': 5},
            'schedule_task': {'queue': 'scheduler', 'priority': 3},
            'notification': {'queue': 'notifications', 'priority': 1},
        },
        
        # Priority queues
        task_queue_max_priority=10,
        task_default_priority=5,
        
        # Task acks optimization
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        
        # Connection pool
        broker_pool_limit=10,
        broker_connection_retry=True,
        broker_connection_retry_on_startup=True,
    )
    
    # Define queues with priorities
    app.conf.task_queues = (
        Queue('execution', Exchange('execution'), routing_key='execution',
              priority=10),
        Queue('scheduler', Exchange('scheduler'), routing_key='scheduler',
              priority=5),
        Queue('notifications', Exchange('notifications'), 
              routing_key='notifications', priority=1),
    )
    
    return app
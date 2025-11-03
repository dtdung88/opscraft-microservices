from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
user_registrations = Counter(
    'auth_user_registrations_total',
    'Total number of user registrations'
)

user_logins = Counter(
    'auth_user_logins_total',
    'Total number of user logins',
    ['status']
)

token_verifications = Counter(
    'auth_token_verifications_total',
    'Total number of token verifications',
    ['status']
)

request_duration = Histogram(
    'auth_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_sessions = Gauge(
    'auth_active_sessions',
    'Number of active user sessions'
)

def init_metrics():
    """Initialize metrics"""
    pass
import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'service'):
            log_data['service'] = record.service
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logger(service_name: str, log_level: str = "INFO"):
    """Setup structured JSON logger"""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Console handler with JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # Add service name to all logs
    logger = logging.LoggerAdapter(logger, {"service": service_name})
    
    return logger
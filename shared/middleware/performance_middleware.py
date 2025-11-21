from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import gzip
import json
from typing import Callable

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Performance optimization middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Enable response compression
        response = await call_next(request)
        
        # Compress responses > 1KB
        if (
            'gzip' in request.headers.get('accept-encoding', '') and
            int(response.headers.get('content-length', 0)) > 1024
        ):
            body = b''
            async for chunk in response.body_iterator:
                body += chunk
            
            compressed = gzip.compress(body)
            
            return Response(
                content=compressed,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    'content-encoding': 'gzip',
                    'content-length': str(len(compressed))
                }
            )
        
        return response

# Batch API endpoint
@router.post("/batch")
async def batch_operations(
    operations: List[BatchOperation],
    db: Session = Depends(get_db)
):
    """Execute multiple operations in a single request"""
    results = []
    
    async with db.begin():
        for op in operations:
            try:
                result = await execute_operation(op, db)
                results.append({"success": True, "data": result})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
    
    return {"results": results}
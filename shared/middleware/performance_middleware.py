from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import gzip
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Performance optimization middleware"""

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        accept_encoding = request.headers.get('accept-encoding', '')
        content_length = response.headers.get('content-length', '0')

        if 'gzip' in accept_encoding and int(content_length) > 1024:
            try:
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
                    },
                    media_type=response.media_type
                )
            except Exception as e:
                logger.error(f"Compression failed: {e}")

        return response
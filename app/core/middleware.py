import time
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('request_count', 'App Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['method', 'endpoint'])

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        start_time = time.time()
        method = scope['method']
        path = scope['path']

        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status = str(message['status'])
                REQUEST_COUNT.labels(method=method, endpoint=path, http_status=status).inc()
            await send(message)

        await self.app(scope, receive, send_wrapper)
        REQUEST_LATENCY.labels(method=method, endpoint=path).observe(time.time() - start_time)
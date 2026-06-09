class SSEMiddleware:
    """Add no-buffering headers to all SSE (text/event-stream) responses.

    Without these headers, reverse proxies (nginx, localtunnel, Cloudflare) buffer the
    entire response body before forwarding it to the browser, which breaks streaming.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get('Content-Type', '')
        if 'text/event-stream' in content_type:
            response['Cache-Control'] = 'no-cache, no-store'
            response['X-Accel-Buffering'] = 'no'
        return response

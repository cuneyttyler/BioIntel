import json

from django.http import StreamingHttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Project
from core.services import claude_client


class AIPanelChatView(APIView):
    """POST /api/projects/<pk>/ai-panel/chat/ — SSE: per-page AI panel chat."""

    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'message required'}, status=400)

        page_type = request.data.get('page_type', 'unknown')
        page_entity = request.data.get('page_entity', {})
        session_messages = request.data.get('session_messages', [])

        def event_stream():
            yield from claude_client.stream_ai_panel_chat(
                project_id=pk,
                page_type=page_type,
                page_entity=page_entity,
                message=message,
                session_messages=session_messages,
            )

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

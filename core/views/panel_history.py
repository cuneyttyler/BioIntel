from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Project, PanelSession, PanelMessage


class PanelHistoryView(APIView):
    """
    GET    /api/projects/<pk>/panel-history/<page_type>/  — list messages
    POST   /api/projects/<pk>/panel-history/<page_type>/  — append a message
    DELETE /api/projects/<pk>/panel-history/<page_type>/  — clear all messages
    """

    def _get_session(self, pk, page_type):
        project = Project.objects.get(pk=pk)
        session, _ = PanelSession.objects.get_or_create(project=project, page_type=page_type)
        return session

    def get(self, request, pk, page_type):
        try:
            session = self._get_session(pk, page_type)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        messages = [
            {
                'role': m.role,
                'content': m.content,
                'suggestion': m.suggestion,
                'ts': int(m.created_at.timestamp() * 1000),
            }
            for m in session.messages.all()
        ]
        return Response({'messages': messages})

    def post(self, request, pk, page_type):
        role = request.data.get('role')
        content = request.data.get('content', '')
        suggestion = request.data.get('suggestion', None)

        if role not in ('user', 'assistant'):
            return Response({'error': 'role must be user or assistant'}, status=400)
        if not content:
            return Response({'error': 'content required'}, status=400)

        try:
            session = self._get_session(pk, page_type)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        msg = PanelMessage.objects.create(
            session=session,
            role=role,
            content=content,
            suggestion=suggestion,
        )
        return Response({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'suggestion': msg.suggestion,
            'ts': int(msg.created_at.timestamp() * 1000),
        }, status=201)

    def delete(self, request, pk, page_type):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        PanelSession.objects.filter(project=project, page_type=page_type).delete()
        return Response(status=204)

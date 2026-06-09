import json
from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import ChatSession, ChatMessage
from core.serializers import ChatSessionSerializer, ChatSessionListSerializer, ChatMessageSerializer
from core.services import claude_client
from core.services.rag import retrieve, format_rag_context


class ChatSessionListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ChatSessionListSerializer
        return ChatSessionSerializer

    def get_queryset(self):
        qs = ChatSession.objects.all().order_by('-updated_at')
        project_id = self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class ChatSessionDetailView(generics.RetrieveDestroyAPIView):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer


class ChatMessageView(APIView):
    def post(self, request, pk):
        try:
            session = ChatSession.objects.get(pk=pk)
        except ChatSession.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'content required'}, status=400)

        ChatMessage.objects.create(session=session, role='user', content=content)

        history = session.messages.order_by('created_at')
        api_messages = [{'role': m.role, 'content': m.content} for m in history]

        project_context = ''
        if session.project_id:
            project_context = claude_client.build_project_context(session.project_id)

        rag_chunks = retrieve(
            query=content,
            project_id=session.project_id if session.project_id else None,
        )
        rag_context = format_rag_context(rag_chunks)

        collected_text = []
        collected_sources = []

        def generate():
            for chunk in claude_client.stream_chat(api_messages, project_context, rag_context, rag_chunks):
                try:
                    payload = json.loads(chunk.removeprefix('data: ').strip())
                    if payload.get('type') == 'text_delta':
                        collected_text.append(payload.get('text', ''))
                    elif payload.get('type') == 'sources':
                        collected_sources.extend(payload.get('sources', []))
                    elif payload.get('type') == 'message_stop':
                        full_text = ''.join(collected_text)
                        ChatMessage.objects.create(
                            session=session,
                            role='assistant',
                            content=full_text,
                            sources=collected_sources,
                        )
                        session.save()
                except Exception:
                    pass
                yield chunk

        response = StreamingHttpResponse(generate(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

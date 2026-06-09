import json

from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AILabSession, AIPlan, Project
from core.serializers import AILabSessionSerializer, AIPlanSerializer
from core.services import ai_plan as ai_plan_service
from core.services import claude_client


class AILabSessionListCreateView(generics.ListCreateAPIView):
    queryset = AILabSession.objects.all().order_by('-created_at')
    serializer_class = AILabSessionSerializer


class AILabSessionDetailView(generics.RetrieveUpdateAPIView):
    queryset = AILabSession.objects.all()
    serializer_class = AILabSessionSerializer


class AILabSessionMessageView(APIView):
    """POST /api/ai-lab/sessions/<pk>/messages/ — SSE: intake chat message."""

    def post(self, request, pk):
        try:
            session = AILabSession.objects.get(pk=pk)
        except AILabSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'message required'}, status=400)

        session_messages = session.messages or []

        collected_text = []
        collected_proposal = {}

        def event_stream():
            import re
            for chunk in claude_client.stream_ai_lab_intake(session.id, message, session_messages):
                yield chunk
                try:
                    data = json.loads(chunk.replace('data: ', '', 1).strip())
                    if data.get('type') == 'text_delta':
                        collected_text.append(data.get('text', ''))
                except Exception:
                    pass

            full_text = ''.join(collected_text)

            proposal_match = re.search(r'<proposal>(.*?)</proposal>', full_text, re.DOTALL)
            if proposal_match:
                try:
                    proposal_json = json.loads(proposal_match.group(1).strip())
                    collected_proposal.update(proposal_json)
                except Exception:
                    pass

            # Persist messages
            session_messages.append({'role': 'user', 'content': message})
            session_messages.append({'role': 'assistant', 'content': full_text})
            session.messages = session_messages

            if collected_proposal:
                session.proposal = collected_proposal

            session.save(update_fields=['messages', 'proposal', 'updated_at'])

            if collected_proposal:
                yield f'data: {json.dumps({"type": "proposal", "proposal": collected_proposal})}\n\n'

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


class AILabSessionCreateProjectView(APIView):
    """POST /api/ai-lab/sessions/<pk>/create-project/ — finalize intake and create Project + AIPlan."""

    def post(self, request, pk):
        try:
            session = AILabSession.objects.get(pk=pk)
        except AILabSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        proposal = session.proposal
        if not proposal:
            return Response({'error': 'No proposal available — complete intake first'}, status=400)

        # Allow overrides from request body
        proposal.update({k: v for k, v in request.data.items() if v})

        project = Project.objects.create(
            name=proposal.get('project_name', 'New AI-Driven Project'),
            description=proposal.get('description', ''),
            pathway=proposal.get('pathway', 'analog_based'),
            molecule_type=proposal.get('molecule_type', 'small_molecule'),
            phase=proposal.get('phase', 'preclinical'),
            mode='ai_driven',
        )

        plan = AIPlan.objects.create(
            project=project,
            molecule_type=proposal.get('molecule_type', 'small_molecule'),
            disease_description=proposal.get('disease_description', ''),
            constraints=proposal.get('constraints', {}),
            status='active',
        )

        steps = ai_plan_service.create_plan_steps(plan.id, plan.molecule_type)
        plan.step_count = len(steps)
        plan.save(update_fields=['step_count'])
        ai_plan_service.advance_plan(plan.id)

        session.status = 'completed'
        session.created_project = project
        session.save(update_fields=['status', 'created_project', 'updated_at'])

        return Response({
            'project_id': project.id,
            'plan_id': plan.id,
            'plan': AIPlanSerializer(plan).data,
        }, status=201)

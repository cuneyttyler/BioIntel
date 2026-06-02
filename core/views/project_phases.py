from django.utils import timezone
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Project, ProjectPhase
from core.serializers import ProjectPhaseSerializer


class ProjectPhaseListView(generics.ListCreateAPIView):
    serializer_class = ProjectPhaseSerializer

    def get_queryset(self):
        return ProjectPhase.objects.filter(project_id=self.kwargs['pk']).order_by('phase')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class ProjectPhaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectPhaseSerializer

    def get_queryset(self):
        return ProjectPhase.objects.filter(project_id=self.kwargs['pk'])

    def get_object(self):
        return ProjectPhase.objects.get(project_id=self.kwargs['pk'], pk=self.kwargs['phase_pk'])


class ProjectPhaseDecisionView(APIView):
    def post(self, request, pk, phase_pk):
        try:
            phase = ProjectPhase.objects.get(project_id=pk, pk=phase_pk)
        except ProjectPhase.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        decision = request.data.get('decision')
        if decision not in ('go', 'no_go'):
            return Response({'error': 'decision must be "go" or "no_go"'}, status=400)

        phase.decision = decision
        phase.decision_rationale = request.data.get('rationale', '')
        phase.decided_at = timezone.now()
        if decision == 'go':
            phase.status = 'complete'
        else:
            phase.status = 'on_hold'
        phase.save()
        return Response(ProjectPhaseSerializer(phase).data)

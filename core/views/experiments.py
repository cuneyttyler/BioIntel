import json
from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Experiment, ExperimentResult
from core.serializers import ExperimentSerializer, ExperimentResultSerializer
from core.services import claude_client


class RecentExperimentsView(generics.ListAPIView):
    serializer_class = ExperimentSerializer

    def get_queryset(self):
        return Experiment.objects.order_by('-created_at')[:10]


class ExperimentListCreateView(generics.ListCreateAPIView):
    serializer_class = ExperimentSerializer

    def get_queryset(self):
        qs = Experiment.objects.all().order_by('-created_at')
        project_id = self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)
        plan_id = self.request.query_params.get('synthesis_plan')
        if plan_id:
            qs = qs.filter(synthesis_plan_id=plan_id)
        return qs


class ExperimentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer


class ExperimentResultsView(generics.ListCreateAPIView):
    serializer_class = ExperimentResultSerializer

    def get_queryset(self):
        return ExperimentResult.objects.filter(experiment_id=self.kwargs['pk']).order_by('-recorded_at')

    def perform_create(self, serializer):
        serializer.save(experiment_id=self.kwargs['pk'])


class ExperimentInterpretView(APIView):
    def post(self, request, pk):
        try:
            experiment = Experiment.objects.get(pk=pk)
        except Experiment.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        latest_result = experiment.results.order_by('-recorded_at').first()
        if not latest_result:
            return Response({'error': 'No results to interpret'}, status=400)

        system = (
            'You are an expert drug development scientist. Interpret the experiment results '
            'in the context of the experiment objective and success criteria. '
            'Recommend one of: optimize, reproduce, scale, or abort. Be concise and specific.'
        )
        user_content = (
            f'Experiment: {experiment.title}\n'
            f'Type: {experiment.experiment_type}\n'
            f'Objective: {experiment.objective}\n'
            f'Success criteria: {experiment.success_criteria}\n'
            f'Variables: {json.dumps(experiment.variables)}\n\n'
            f'Results:\n{json.dumps(latest_result.result_data, indent=2)}\n'
            f'Notes: {latest_result.notes}'
        )

        def generate():
            for chunk in claude_client.generate_once(system, user_content):
                yield chunk

        response = StreamingHttpResponse(generate(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

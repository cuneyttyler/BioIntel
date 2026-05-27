import json
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Project, RiskAssessment
from core.serializers import RiskAssessmentSerializer
from core.services import claude_client, clinicaltrials, pubmed


class RiskAssessmentView(APIView):
    def get(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        assessment = project.risk_assessments.order_by('-updated_at').first()
        if not assessment:
            return Response(None)
        return Response(RiskAssessmentSerializer(assessment).data)

    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        assessment, _ = RiskAssessment.objects.get_or_create(project=project)
        serializer = RiskAssessmentSerializer(assessment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GenerateRiskAssessmentView(APIView):
    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        context = claude_client.build_project_context(pk)
        compounds = project.compounds.all()
        compound_name = compounds[0].name if compounds else ''

        trials_data = {}
        literature_data = {}
        if compound_name:
            trials_data = clinicaltrials.search_trials(intervention=compound_name)
            pmids = pubmed.search_articles(f'{compound_name} safety toxicity', max_results=5)
            literature_data = {'pmids': pmids}

        system = (
            'You are an expert pharmaceutical risk analyst. Generate a structured risk assessment '
            'for the drug development project. Return a JSON object with:\n'
            '{"risk_factors": [{"category": "...", "level": "low|medium|high|critical", '
            '"probability": 1-5, "impact": 1-5, "rationale": "..."}], '
            '"risk_heat_map": {"high_probability_high_impact": [], ...}}\n'
            'After the JSON, provide a brief narrative summary.'
        )
        user_content = (
            f'{context}\n\n'
            f'Clinical precedent: {json.dumps(trials_data)[:1000]}\n'
            f'Literature: {json.dumps(literature_data)}'
        )

        def generate():
            for chunk in claude_client.generate_once(system, user_content):
                yield chunk

        response = StreamingHttpResponse(generate(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

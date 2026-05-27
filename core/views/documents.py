import json
from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Project, Document
from core.serializers import DocumentSerializer
from core.services import claude_client, dailymed, openfda


class ProjectDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(project_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class GenerateDocumentView(APIView):
    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        doc_type = request.data.get('doc_type', 'process_summary')
        context = claude_client.build_project_context(pk)

        risk = project.risk_assessments.order_by('-updated_at').first()
        risk_summary = json.dumps(risk.risk_factors[:5]) if risk else 'No risk assessment available'

        compound_name = ''
        compounds = project.compounds.all()
        if compounds:
            compound_name = compounds[0].name

        label_data = dailymed.search_spls(compound_name) if compound_name else []
        guidance_data = openfda.search_guidance('process validation CMC')

        doc_type_prompts = {
            'process_summary': 'a regulatory-ready process summary including rationale, key decision points, and recommended next milestones',
            'risk_report': 'a risk assessment report with risk factor analysis, mitigation strategies, and regulatory considerations',
            'handoff': 'a development handoff note summarizing process history, current status, and next-phase recommendations for manufacturing and regulatory teams',
        }
        doc_description = doc_type_prompts.get(doc_type, 'a process development document')

        system = (
            'You are an expert drug development scientist and technical writer. '
            'Generate a structured Markdown document formatted for regulatory review. '
            'Use clear section headers (##), bullet points for lists, and bold for critical information. '
            'Be specific and actionable.'
        )
        user_content = (
            f'Generate {doc_description} for the following project:\n\n'
            f'{context}\n\n'
            f'Risk factors: {risk_summary}\n\n'
            f'Relevant FDA guidance: {json.dumps([g.get("title", "") for g in guidance_data[:3]])}\n\n'
            f'Drug labeling reference: {json.dumps(label_data[:2])}'
        )

        def generate():
            for chunk in claude_client.generate_once(system, user_content):
                yield chunk

        response = StreamingHttpResponse(generate(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class DocumentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class DocumentExportView(APIView):
    def post(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        from django.http import HttpResponse
        response = HttpResponse(document.content, content_type='text/markdown')
        filename = document.title.replace(' ', '_') or 'document'
        response['Content-Disposition'] = f'attachment; filename="{filename}.md"'
        return response

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
            'analog_report': (
                'an analog development report covering: (1) reference drug profile and mechanism of action, '
                '(2) patent landscape — which structural and process patents apply, '
                '(3) selected analog rationale — why this structure avoids existing patents while preserving the therapeutic mechanism, '
                '(4) ADMET comparison between the reference drug and the analog candidate, '
                '(5) proposed synthesis route for the analog'
            ),
            'formulation_report': (
                'a pharmaceutical formulation development report following ICH Q8(R2) principles covering: '
                '(1) dosage form and route of administration rationale, '
                '(2) composition table with IIG compliance for each excipient, '
                '(3) API-excipient compatibility assessment, '
                '(4) manufacturing process description and critical process parameters, '
                '(5) container closure system justification, '
                '(6) recommended next development steps'
            ),
            'stability_summary': (
                'a stability summary report per ICH Q1A(R2) covering: '
                '(1) material description and intended storage condition, '
                '(2) stability study design (conditions, timepoints, attributes tested), '
                '(3) results summary with assay trends and degradation product profiles, '
                '(4) any OOS or OOT results with investigation summary, '
                '(5) proposed shelf life and label storage condition, '
                '(6) conclusions and recommendations'
            ),
            'admet_summary': (
                'an ADMET/pharmacokinetics summary report covering: '
                '(1) in-silico ADMET predictions (pkCSM) with flag thresholds, '
                '(2) experimental measurements if available, '
                '(3) comparison against benchmark criteria (lead drug or literature), '
                '(4) key liabilities identified (hERG, P-gp efflux, CYP inhibition, hepatotoxicity), '
                '(5) preclinical PK parameters if available, '
                '(6) overall druggability assessment and recommended mitigation strategies'
            ),
            'ind_cmc': (
                'an IND CMC (Chemistry, Manufacturing, and Controls) section per 21 CFR 312.23(a)(7) covering: '
                '## 3.2.S — Drug Substance\n'
                '- Nomenclature, structure, general properties\n'
                '- Manufacturing process and process controls\n'
                '- Characterization (structure confirmation, physicochemical properties)\n'
                '- Specifications and analytical procedures\n'
                '- Reference standard description\n'
                '- Container closure system\n'
                '- Stability summary and conclusions\n\n'
                '## 3.2.P — Drug Product\n'
                '- Description and composition\n'
                '- Pharmaceutical development rationale\n'
                '- Manufacturing process description\n'
                '- Control of excipients (IIG compliance)\n'
                '- Drug product specifications\n'
                '- Container closure system\n'
                '- Stability summary'
            ),
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

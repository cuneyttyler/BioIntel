from rest_framework.views import APIView
from rest_framework.response import Response
from core.services import opentargets, uniprot


class DiseaseSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response([])
        results = opentargets.search_disease(q)
        return Response(results)


class DiseaseTargetsView(APIView):
    def get(self, request, efo_id):
        data = opentargets.get_disease_targets(efo_id)
        return Response(data)


class DiseaseDrugsView(APIView):
    def get(self, request, efo_id):
        data = opentargets.get_disease_drugs(efo_id)
        return Response(data)


class TargetDetailView(APIView):
    def get(self, request, gene_symbol):
        results = uniprot.search_protein(gene_symbol)
        return Response(results[0] if results else {})

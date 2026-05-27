from rest_framework.views import APIView
from rest_framework.response import Response
from core.services import openfda, dailymed


class GuidanceSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response([])
        results = openfda.search_guidance(q)
        return Response(results)


class DrugLabelsView(APIView):
    def get(self, request):
        drug = request.query_params.get('drug', '').strip()
        if not drug:
            return Response([])
        results = dailymed.search_spls(drug)
        return Response(results)


class NDCView(APIView):
    def get(self, request):
        drug = request.query_params.get('drug', '').strip()
        if not drug:
            return Response([])
        results = openfda.get_ndc(drug)
        return Response(results)


class ExcipientsView(APIView):
    def get(self, request):
        dosage_form = request.query_params.get('form', '').strip()
        if not dosage_form:
            return Response([])
        results = openfda.get_excipients(dosage_form)
        return Response(results)

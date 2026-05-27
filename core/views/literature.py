from rest_framework.views import APIView
from rest_framework.response import Response
from core.services import pubmed, clinicaltrials


class LiteratureSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        max_results = int(request.query_params.get('max', 20))
        if not q:
            return Response([])
        pmids = pubmed.search_articles(q, max_results)
        summaries = pubmed.get_summaries(pmids)
        return Response(summaries)


class ArticleDetailView(APIView):
    def get(self, request, pmid):
        data = pubmed.fetch_abstract(str(pmid))
        return Response(data)


class TrialSearchView(APIView):
    def get(self, request):
        condition = request.query_params.get('condition', '')
        intervention = request.query_params.get('intervention', '')
        phase = request.query_params.get('phase', '')
        data = clinicaltrials.search_trials(
            condition=condition or None,
            intervention=intervention or None,
            phase=phase or None,
        )
        return Response(data)


class TrialDetailView(APIView):
    def get(self, request, nct_id):
        data = clinicaltrials.get_trial(nct_id)
        return Response(data)

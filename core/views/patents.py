from rest_framework.views import APIView
from rest_framework.response import Response
from core.services import surechembl, espacenet


class PatentSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        smiles = request.query_params.get('smiles', '').strip()
        if smiles:
            results = surechembl.search_by_smiles(smiles)
        elif q:
            results = surechembl.search_compound(q)
        else:
            return Response([])
        return Response(results)


class PatentDetailView(APIView):
    def get(self, request, patent_number):
        data = espacenet.get_patent(patent_number)
        return Response(data)

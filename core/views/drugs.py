from rest_framework.views import APIView
from rest_framework.response import Response
from core.services import chembl, dailymed, pubmed, clinicaltrials, surechembl


class DrugSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response([])
        results = chembl.search_molecule(q)
        return Response(results)


class DrugDetailView(APIView):
    def get(self, request, chembl_id):
        molecule = chembl.get_molecule(chembl_id)
        if not molecule:
            return Response({'error': 'Drug not found'}, status=404)

        mechanisms = chembl.get_mechanisms(chembl_id)

        # Get common name for DailyMed lookup
        name = (
            molecule.get('pref_name')
            or (molecule.get('molecule_synonyms') or [{}])[0].get('molecule_synonym', chembl_id)
        )

        spls = []
        spl_detail = {}
        try:
            spls = dailymed.search_spls(name)
            if spls:
                set_id = spls[0].get('setid')
                if set_id:
                    spl_detail = dailymed.get_spl(set_id)
        except Exception:
            pass

        return Response({
            'molecule': molecule,
            'mechanisms': mechanisms,
            'formulation': {
                'spls': spls[:3],
                'label': spl_detail,
            },
        })


class DrugSynthesisView(APIView):
    def get(self, request, chembl_id):
        molecule = chembl.get_molecule(chembl_id)
        name = molecule.get('pref_name', chembl_id) if molecule else chembl_id
        pmids = pubmed.search_articles(f'{name} synthesis route', max_results=10)
        articles = pubmed.get_summaries(pmids)
        return Response(articles)


class DrugTrialsView(APIView):
    def get(self, request, chembl_id):
        molecule = chembl.get_molecule(chembl_id)
        name = molecule.get('pref_name', chembl_id) if molecule else chembl_id
        data = clinicaltrials.search_trials(intervention=name)
        studies = data.get('studies', []) if isinstance(data, dict) else []
        return Response(studies)


class DrugPatentsView(APIView):
    def get(self, request, chembl_id):
        molecule = chembl.get_molecule(chembl_id)
        name = molecule.get('pref_name', chembl_id) if molecule else chembl_id
        patents = surechembl.search_compound(name)
        return Response(patents)

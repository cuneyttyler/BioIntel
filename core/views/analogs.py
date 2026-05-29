from concurrent.futures import ThreadPoolExecutor, as_completed

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import DrugInvestigation, AnalogCandidate
from core.serializers import DrugInvestigationSerializer, AnalogCandidateSerializer
from core.services import pubchem, pkcsm, surechembl


class AnalogSearchView(APIView):
    def post(self, request):
        smiles = request.data.get('smiles', '').strip()
        threshold = float(request.data.get('threshold', 0.7))
        if not smiles:
            return Response({'error': 'smiles is required'}, status=400)

        props_list = pubchem.get_similar_compounds(smiles, threshold=threshold)
        results = [
            {
                'cid': p.get('CID'),
                'smiles': p.get('IsomericSMILES') or p.get('SMILES', ''),
                'similarity_score': threshold,
            }
            for p in props_list
        ]
        return Response(results)


class AnalogPatentCheckView(APIView):
    def post(self, request):
        candidates = request.data.get('candidates', [])
        if not candidates:
            return Response({'error': 'candidates is required'}, status=400)

        def check_one(candidate):
            cid = candidate.get('cid')
            smiles = candidate.get('smiles', '')
            if cid:
                ids = surechembl._get_patent_ids_by_cid(int(cid))
                status = 'covered' if ids else 'free'
                refs = ids[:5]
            else:
                status = surechembl.get_patent_status(smiles)
                refs = []
            return {'cid': cid, 'smiles': smiles, 'patent_status': status, 'patent_refs': refs}

        output = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(check_one, c): c for c in candidates}
            for future in as_completed(futures):
                try:
                    output.append(future.result())
                except Exception:
                    c = futures[future]
                    output.append({'cid': c.get('cid'), 'smiles': c.get('smiles', ''), 'patent_status': 'unknown', 'patent_refs': []})

        return Response(output)


class AnalogADMETView(APIView):
    def post(self, request):
        smiles_list = request.data.get('smiles_list', [])
        if not smiles_list:
            return Response({'error': 'smiles_list is required'}, status=400)

        def predict_one(smiles):
            result = pkcsm.predict_admet(smiles)
            return {'smiles': smiles, 'admet': result}

        output = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(predict_one, s): s for s in smiles_list}
            for future in as_completed(futures):
                try:
                    output.append(future.result())
                except Exception:
                    output.append({'smiles': futures[future], 'admet': {}})

        return Response(output)


class InvestigationListCreateView(generics.ListCreateAPIView):
    queryset = DrugInvestigation.objects.all().order_by('-created_at')
    serializer_class = DrugInvestigationSerializer


class InvestigationDetailView(generics.RetrieveUpdateAPIView):
    queryset = DrugInvestigation.objects.all()
    serializer_class = DrugInvestigationSerializer


class InvestigationLinkProjectView(APIView):
    """Link an investigation (and optionally its shortlisted candidates) to a project."""

    def post(self, request, pk):
        try:
            investigation = DrugInvestigation.objects.get(pk=pk)
        except DrugInvestigation.DoesNotExist:
            return Response({'error': 'Investigation not found'}, status=404)

        project_id = request.data.get('project')
        if not project_id:
            return Response({'error': 'project is required'}, status=400)

        investigation.project_id = project_id
        investigation.save(update_fields=['project'])

        if request.data.get('link_shortlisted', True):
            AnalogCandidate.objects.filter(investigation=investigation, shortlisted=True).update(project_id=project_id)

        return Response({'status': 'linked', 'investigation': pk, 'project': project_id})


class AnalogCandidateDetailView(generics.RetrieveUpdateAPIView):
    """PATCH individual analog candidate (e.g. toggle shortlisted, set project)."""
    queryset = AnalogCandidate.objects.all()
    serializer_class = AnalogCandidateSerializer


class AnalogCandidateView(APIView):
    def get(self, request, pk):
        candidates = AnalogCandidate.objects.filter(investigation_id=pk).order_by('-similarity_score')
        return Response(AnalogCandidateSerializer(candidates, many=True).data)

    def post(self, request, pk):
        try:
            investigation = DrugInvestigation.objects.get(pk=pk)
        except DrugInvestigation.DoesNotExist:
            return Response({'error': 'Investigation not found'}, status=404)
        serializer = AnalogCandidateSerializer(data={**request.data, 'investigation': investigation.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(investigation=investigation)
        return Response(serializer.data, status=201)

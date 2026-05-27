import requests as http_requests
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Compound
from core.serializers import CompoundSerializer
from core.services import pubchem, chembl, pkcsm, comptox, uniprot, nist


class CompoundSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response([])
        pubchem_results = pubchem.search_compound(q)
        chembl_results = chembl.search_molecule(q)
        return Response({'pubchem': pubchem_results, 'chembl': chembl_results[:5]})


class CompoundListCreateView(generics.ListCreateAPIView):
    serializer_class = CompoundSerializer

    def get_queryset(self):
        qs = Compound.objects.all()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class CompoundDetailView(generics.RetrieveAPIView):
    queryset = Compound.objects.all()
    serializer_class = CompoundSerializer


class CompoundPropertiesView(APIView):
    def get(self, request, pk):
        try:
            compound = Compound.objects.get(pk=pk)
        except Compound.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        if compound.pubchem_cid:
            data = pubchem.get_compound_properties(compound.pubchem_cid)
        else:
            data = {}
        return Response(data)


class CompoundADMETView(APIView):
    def get(self, request, pk):
        try:
            compound = Compound.objects.get(pk=pk)
        except Compound.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        if not compound.smiles:
            return Response({'error': 'No SMILES available'}, status=400)
        data = pkcsm.predict_admet(compound.smiles)
        return Response(data)


class CompoundSafetyView(APIView):
    def get(self, request, pk):
        try:
            compound = Compound.objects.get(pk=pk)
        except Compound.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        details = comptox.get_chemical_details(compound.name)
        dtxsid = ''
        if isinstance(details, list) and details:
            dtxsid = details[0].get('dtxsid', '')
        hazard = comptox.get_hazard_data(dtxsid) if dtxsid else {}
        bioassay = comptox.get_bioassay_summary(dtxsid) if dtxsid else {}
        return Response({'details': details, 'hazard': hazard, 'bioassay': bioassay})


class CompoundTargetsView(APIView):
    def get(self, request, pk):
        try:
            compound = Compound.objects.get(pk=pk)
        except Compound.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        mechanisms = []
        if compound.chembl_id:
            mechanisms = chembl.get_mechanisms(compound.chembl_id)
        targets = []
        for mech in mechanisms[:5]:
            uniprot_ids = []
            for target in mech.get('target_components', []):
                accession = target.get('accession')
                if accession:
                    uniprot_ids.append(accession)
            for uid in uniprot_ids[:2]:
                protein = uniprot.get_protein(uid)
                if protein:
                    targets.append({'mechanism': mech, 'uniprot': protein})
        return Response({'mechanisms': mechanisms, 'targets': targets})


class CompoundStructureView(APIView):
    def get(self, request, pk):
        try:
            compound = Compound.objects.get(pk=pk)
        except Compound.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        if not compound.pubchem_cid:
            return Response({'error': 'No PubChem CID'}, status=400)
        url = pubchem.structure_png_url(compound.pubchem_cid)
        try:
            r = http_requests.get(url, timeout=15)
            r.raise_for_status()
            return HttpResponse(r.content, content_type='image/png')
        except Exception:
            return Response({'error': 'Could not fetch structure'}, status=502)


class CompoundSimilarView(APIView):
    def get(self, request, pk):
        try:
            compound = Compound.objects.get(pk=pk)
        except Compound.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        if not compound.smiles:
            return Response([])
        cids = pubchem.get_similar_compounds(compound.smiles)
        return Response(cids)


class CompoundSpectraView(APIView):
    def get(self, request):
        cas = request.query_params.get('cas', '')
        spec_type = request.query_params.get('type', 'IR')
        if not cas:
            return Response({'error': 'cas parameter required'}, status=400)
        jcamp = nist.get_spectrum(cas, spec_type)
        return Response({'jcamp': jcamp})

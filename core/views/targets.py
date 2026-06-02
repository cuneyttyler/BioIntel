from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import TargetProfile
from core.serializers import TargetProfileSerializer
from core.services import pdb, uniprot


class TargetProfileListCreateView(generics.ListCreateAPIView):
    queryset = TargetProfile.objects.all().order_by('-created_at')
    serializer_class = TargetProfileSerializer


class TargetProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TargetProfile.objects.all()
    serializer_class = TargetProfileSerializer


class TargetPDBView(APIView):
    def get(self, request, pk):
        try:
            profile = TargetProfile.objects.get(pk=pk)
        except TargetProfile.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        structures = pdb.search_structures(profile.uniprot_id)
        pdb_ids = [s['pdb_id'] for s in structures]

        profile.pdb_ids = pdb_ids
        profile.save(update_fields=['pdb_ids'])

        return Response({'uniprot_id': profile.uniprot_id, 'pdb_ids': pdb_ids, 'structures': structures})


class TargetBindingSitesView(APIView):
    def get(self, request, pk):
        try:
            profile = TargetProfile.objects.get(pk=pk)
        except TargetProfile.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        pdb_id = request.query_params.get('pdb_id') or profile.selected_pdb_id
        if not pdb_id:
            return Response({'error': 'No PDB ID specified'}, status=400)

        sites = pdb.get_binding_sites(pdb_id)
        return Response({'pdb_id': pdb_id, 'sites': sites})

    def post(self, request, pk):
        """Save binding site definition to the target profile."""
        try:
            profile = TargetProfile.objects.get(pk=pk)
        except TargetProfile.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        profile.selected_pdb_id = request.data.get('pdb_id', profile.selected_pdb_id)
        profile.binding_site_definition = request.data.get('binding_site', profile.binding_site_definition)
        profile.save(update_fields=['selected_pdb_id', 'binding_site_definition'])
        return Response(TargetProfileSerializer(profile).data)


class TargetUniProtView(APIView):
    def get(self, request, pk):
        try:
            profile = TargetProfile.objects.get(pk=pk)
        except TargetProfile.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        data = uniprot.get_protein(profile.uniprot_id)
        return Response(data)

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import VirtualScreeningRun, VirtualScreeningHit, TargetProfile
from core.serializers import VirtualScreeningRunSerializer, VirtualScreeningHitSerializer
from core.services import zinc, autodock


class VirtualScreeningRunListCreateView(generics.ListCreateAPIView):
    serializer_class = VirtualScreeningRunSerializer

    def get_queryset(self):
        qs = VirtualScreeningRun.objects.all().order_by('-created_at')
        target_id = self.request.query_params.get('target_profile_id')
        if target_id:
            qs = qs.filter(target_profile_id=target_id)
        return qs

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        run_id = response.data['id']
        run = VirtualScreeningRun.objects.get(pk=run_id)

        try:
            profile = TargetProfile.objects.get(pk=run.target_profile_id)
        except TargetProfile.DoesNotExist:
            return response

        library = run.library
        if library == 'fda_approved':
            smiles_list = [s['smiles'] for s in zinc.get_fda_approved(limit=1000)]
        elif library == 'clinical_candidates':
            smiles_list = [s['smiles'] for s in zinc.get_clinical_candidates(limit=1000)]
        elif library == 'fragments':
            smiles_list = [s['smiles'] for s in zinc.get_fragment_library(limit=1000)]
        elif library == 'custom' and run.custom_smiles:
            smiles_list = run.custom_smiles if isinstance(run.custom_smiles, list) else []
        else:
            smiles_list = []

        if smiles_list and profile.selected_pdb_id and profile.binding_site_definition:
            autodock.run_screening(
                run_id=run_id,
                smiles_list=smiles_list,
                receptor_pdb_id=profile.selected_pdb_id,
                binding_site=profile.binding_site_definition,
            )

        return response


class VirtualScreeningRunDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VirtualScreeningRun.objects.all()
    serializer_class = VirtualScreeningRunSerializer


class VirtualScreeningRunPollView(APIView):
    def get(self, request, pk):
        try:
            run = VirtualScreeningRun.objects.get(pk=pk)
        except VirtualScreeningRun.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response({
            'id': run.id,
            'status': run.status,
            'result_count': run.result_count,
            'error_message': run.error_message,
            'completed_at': run.completed_at,
        })


class VirtualScreeningHitListView(generics.ListAPIView):
    serializer_class = VirtualScreeningHitSerializer

    def get_queryset(self):
        qs = VirtualScreeningHit.objects.filter(run_id=self.kwargs['pk'])
        shortlisted = self.request.query_params.get('shortlisted')
        if shortlisted == 'true':
            qs = qs.filter(shortlisted=True)
        return qs.order_by('docking_score')


class VirtualScreeningHitShortlistView(APIView):
    def patch(self, request, pk):
        try:
            hit = VirtualScreeningHit.objects.get(pk=pk)
        except VirtualScreeningHit.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        hit.shortlisted = request.data.get('shortlisted', not hit.shortlisted)
        hit.save(update_fields=['shortlisted'])
        return Response(VirtualScreeningHitSerializer(hit).data)

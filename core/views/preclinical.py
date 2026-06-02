from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import PreclinicalStudy, Compound, CompoundProperty
from core.serializers import PreclinicalStudySerializer


class PreclinicalStudyListCreateView(generics.ListCreateAPIView):
    serializer_class = PreclinicalStudySerializer

    def get_queryset(self):
        return PreclinicalStudy.objects.filter(project_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class PreclinicalStudyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PreclinicalStudy.objects.all()
    serializer_class = PreclinicalStudySerializer


class PreclinicalStudyResultsView(APIView):
    def get(self, request, pk):
        try:
            study = PreclinicalStudy.objects.get(pk=pk)
        except PreclinicalStudy.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        return Response({
            'study': PreclinicalStudySerializer(study).data,
            'key_findings': study.key_findings,
            'mtd_mgkg': study.mtd_mgkg,
        })

    def patch(self, request, pk):
        """Log findings and key result fields for a completed study."""
        try:
            study = PreclinicalStudy.objects.get(pk=pk)
        except PreclinicalStudy.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        for field in ('key_findings', 'mtd_mgkg', 'noael_mgkg', 'status', 'conclusion', 'results_summary'):
            if field in request.data:
                setattr(study, field, request.data[field])
        study.save()
        return Response(PreclinicalStudySerializer(study).data)


class ADMETDashboardView(APIView):
    def get(self, request, pk):
        """
        Aggregate ADMET data for a project:
        - Computed (pkCSM) from CompoundProperty records
        - Experimental measurements from PreclinicalStudy key_findings
        """
        compounds = Compound.objects.filter(project_id=pk)
        computed_admet = {}
        for compound in compounds:
            admet_props = CompoundProperty.objects.filter(
                compound=compound, property_type='admet'
            ).order_by('-fetched_at').first()
            if admet_props:
                computed_admet[compound.name] = {
                    'compound_id': compound.id,
                    'smiles': compound.smiles,
                    'data': admet_props.data,
                    'source': admet_props.source,
                }

        studies = PreclinicalStudy.objects.filter(project_id=pk)
        experimental = []
        for study in studies:
            if study.key_findings:
                experimental.append({
                    'study_id': study.id,
                    'study_type': study.study_type,
                    'species': study.species,
                    'mtd_mgkg': study.mtd_mgkg,
                    'findings': study.key_findings,
                })

        return Response({
            'project_id': pk,
            'computed_admet': computed_admet,
            'experimental': experimental,
        })


class PreclinicalContextView(APIView):
    def get(self, request, pk):
        try:
            study = PreclinicalStudy.objects.get(pk=pk)
        except PreclinicalStudy.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        return Response({
            'study': PreclinicalStudySerializer(study).data,
        })

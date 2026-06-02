from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import AnalyticalMethod, Specification
from core.serializers import AnalyticalMethodSerializer, SpecificationSerializer


class AnalyticalMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = AnalyticalMethodSerializer

    def get_queryset(self):
        return AnalyticalMethod.objects.filter(project_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class AnalyticalMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AnalyticalMethod.objects.all()
    serializer_class = AnalyticalMethodSerializer


class AnalyticalMethodValidationView(APIView):
    """Return ICH Q2(R1) validation checklist status for a method."""
    ICH_CHECKLIST = {
        'hplc': ['specificity', 'linearity', 'range', 'accuracy', 'precision', 'detection_limit', 'quantitation_limit', 'robustness'],
        'gc': ['specificity', 'linearity', 'range', 'accuracy', 'precision', 'detection_limit', 'quantitation_limit', 'robustness'],
        'nmr': ['specificity', 'linearity', 'accuracy', 'precision'],
        'dissolution': ['specificity', 'linearity', 'range', 'accuracy', 'precision', 'robustness'],
        'default': ['specificity', 'linearity', 'accuracy', 'precision', 'robustness'],
    }

    def get(self, request, pk):
        try:
            method = AnalyticalMethod.objects.get(pk=pk)
        except AnalyticalMethod.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        checklist_items = self.ICH_CHECKLIST.get(method.method_type, self.ICH_CHECKLIST['default'])
        protocol = method.protocol or {}
        completed = [item for item in checklist_items if protocol.get(item)]

        return Response({
            'method_id': pk,
            'method_type': method.method_type,
            'validation_status': method.validation_status,
            'checklist': checklist_items,
            'completed': completed,
            'missing': [item for item in checklist_items if item not in completed],
            'completion_pct': round(len(completed) / len(checklist_items) * 100) if checklist_items else 0,
        })


class SpecificationListCreateView(generics.ListCreateAPIView):
    serializer_class = SpecificationSerializer

    def get_queryset(self):
        return Specification.objects.filter(project_id=self.kwargs['pk']).order_by('spec_type', 'attribute')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class SpecificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Specification.objects.all()
    serializer_class = SpecificationSerializer

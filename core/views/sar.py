from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import SAREntry
from core.serializers import SAREntrySerializer


class SAREntryListCreateView(generics.ListCreateAPIView):
    serializer_class = SAREntrySerializer

    def get_queryset(self):
        return SAREntry.objects.filter(project_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class SAREntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SAREntry.objects.all()
    serializer_class = SAREntrySerializer


class ProjectSARHeatmapView(APIView):
    def get(self, request, pk):
        entries = SAREntry.objects.filter(project_id=pk).exclude(
            r_group='', activity_value=None
        ).values('r_group', 'activity_value', 'activity_type', 'activity_unit', 'smiles')

        r_groups = {}
        for e in entries:
            rg = e['r_group'] or 'core'
            if rg not in r_groups:
                r_groups[rg] = []
            r_groups[rg].append({
                'smiles': e['smiles'],
                'value': e['activity_value'],
                'type': e['activity_type'],
                'unit': e['activity_unit'],
            })

        return Response({'r_groups': r_groups, 'entry_count': len(list(entries))})

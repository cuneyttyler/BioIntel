from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import SaltPolymorphScreen, SaltScreenCandidate, SaltScreenExperiment
from core.serializers import (
    SaltPolymorphScreenSerializer, SaltScreenCandidateSerializer, SaltScreenExperimentSerializer,
)
from core.services import ccdc


class SaltScreenListCreateView(generics.ListCreateAPIView):
    serializer_class = SaltPolymorphScreenSerializer

    def get_queryset(self):
        return SaltPolymorphScreen.objects.filter(project_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class SaltScreenDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaltPolymorphScreen.objects.all()
    serializer_class = SaltPolymorphScreenSerializer


class SaltScreenCandidateView(APIView):
    def get(self, request, pk):
        candidates = SaltScreenCandidate.objects.filter(screen_id=pk).order_by('id')
        return Response(SaltScreenCandidateSerializer(candidates, many=True).data)

    def post(self, request, pk):
        try:
            screen = SaltPolymorphScreen.objects.get(pk=pk)
        except SaltPolymorphScreen.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = SaltScreenCandidateSerializer(data={**request.data, 'screen': screen.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(screen=screen)
        return Response(serializer.data, status=201)


class SaltScreenCandidateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaltScreenCandidate.objects.all()
    serializer_class = SaltScreenCandidateSerializer


class SaltScreenExperimentView(APIView):
    def get(self, request, pk):
        experiments = SaltScreenExperiment.objects.filter(screen_id=pk).order_by('id')
        return Response(SaltScreenExperimentSerializer(experiments, many=True).data)

    def post(self, request, pk):
        try:
            screen = SaltPolymorphScreen.objects.get(pk=pk)
        except SaltPolymorphScreen.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = SaltScreenExperimentSerializer(data={**request.data, 'screen': screen.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(screen=screen)
        return Response(serializer.data, status=201)


class SaltScreenExperimentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaltScreenExperiment.objects.all()
    serializer_class = SaltScreenExperimentSerializer


class CCDCLookupView(APIView):
    def get(self, request):
        smiles = request.query_params.get('smiles', '')
        identifier = request.query_params.get('identifier', '')

        if identifier:
            data = ccdc.get_crystal_data(identifier)
            return Response(data)
        elif smiles:
            results = ccdc.search_structures(smiles)
            return Response({'results': results})
        else:
            return Response({'error': 'Provide smiles or identifier parameter'}, status=400)

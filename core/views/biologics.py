from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    BiologicsCharacterizationMethod, BiologicsFormulation,
    BioprocessDevelopment, CellLineDevelopment, DownstreamPurification,
    Project,
)
from core.serializers import (
    BiologicsCharacterizationMethodSerializer, BiologicsFormulationSerializer,
    BioprocessDevelopmentSerializer, CellLineDevelopmentSerializer,
    DownstreamPurificationSerializer,
)


class ProjectCellLineView(APIView):
    def get(self, request, pk):
        items = CellLineDevelopment.objects.filter(project_id=pk).order_by('-created_at')
        return Response(CellLineDevelopmentSerializer(items, many=True).data)

    def post(self, request, pk):
        s = CellLineDevelopmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(project_id=pk)
        return Response(s.data, status=201)


class CellLineDevelopmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CellLineDevelopment.objects.all()
    serializer_class = CellLineDevelopmentSerializer


class ProjectBioprocessView(APIView):
    def get(self, request, pk):
        items = BioprocessDevelopment.objects.filter(project_id=pk).order_by('-created_at')
        return Response(BioprocessDevelopmentSerializer(items, many=True).data)

    def post(self, request, pk):
        s = BioprocessDevelopmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(project_id=pk)
        return Response(s.data, status=201)


class BioprocessDevelopmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BioprocessDevelopment.objects.all()
    serializer_class = BioprocessDevelopmentSerializer


class ProjectPurificationView(APIView):
    def get(self, request, pk):
        items = DownstreamPurification.objects.filter(project_id=pk).order_by('-created_at')
        return Response(DownstreamPurificationSerializer(items, many=True).data)

    def post(self, request, pk):
        s = DownstreamPurificationSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(project_id=pk)
        return Response(s.data, status=201)


class DownstreamPurificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DownstreamPurification.objects.all()
    serializer_class = DownstreamPurificationSerializer


class ProjectBiologicsFormulationView(APIView):
    def get(self, request, pk):
        items = BiologicsFormulation.objects.filter(project_id=pk).order_by('-created_at')
        return Response(BiologicsFormulationSerializer(items, many=True).data)

    def post(self, request, pk):
        s = BiologicsFormulationSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(project_id=pk)
        return Response(s.data, status=201)


class BiologicsFormulationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BiologicsFormulation.objects.all()
    serializer_class = BiologicsFormulationSerializer


class ProjectBiologicsAnalyticsView(APIView):
    def get(self, request, pk):
        items = BiologicsCharacterizationMethod.objects.filter(project_id=pk).order_by('-created_at')
        return Response(BiologicsCharacterizationMethodSerializer(items, many=True).data)

    def post(self, request, pk):
        s = BiologicsCharacterizationMethodSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(project_id=pk)
        return Response(s.data, status=201)


class BiologicsCharacterizationMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BiologicsCharacterizationMethod.objects.all()
    serializer_class = BiologicsCharacterizationMethodSerializer

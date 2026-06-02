from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import FormulationPlan, FormulationComponent, CompatibilityFlag, Excipient
from core.serializers import (
    FormulationPlanSerializer, FormulationComponentSerializer,
    CompatibilityFlagSerializer, ExcipientSerializer,
)


class FormulationPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = FormulationPlanSerializer

    def get_queryset(self):
        return FormulationPlan.objects.filter(project_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class FormulationPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FormulationPlan.objects.all()
    serializer_class = FormulationPlanSerializer


class FormulationComponentView(APIView):
    def get(self, request, pk):
        components = FormulationComponent.objects.filter(formulation_plan_id=pk)
        return Response(FormulationComponentSerializer(components, many=True).data)

    def post(self, request, pk):
        try:
            plan = FormulationPlan.objects.get(pk=pk)
        except FormulationPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = FormulationComponentSerializer(data={**request.data, 'formulation_plan': plan.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(formulation_plan=plan)
        return Response(serializer.data, status=201)

    def delete(self, request, pk, component_pk):
        try:
            component = FormulationComponent.objects.get(pk=component_pk, formulation_plan_id=pk)
        except FormulationComponent.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        component.delete()
        return Response(status=204)


class CompatibilityCheckView(APIView):
    def post(self, request, pk):
        """
        Check API-excipient compatibility for all components in a formulation plan.
        Returns a list of known incompatibility flags based on the excipient library.
        """
        try:
            plan = FormulationPlan.objects.get(pk=pk)
        except FormulationPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        components = FormulationComponent.objects.filter(formulation_plan=plan)
        component_names = [c.name.lower() for c in components]

        new_flags = []
        for excipient in Excipient.objects.filter(name__in=[c.name for c in components]):
            for incompatible in excipient.incompatibilities:
                incompatible_lower = incompatible.lower()
                for comp_name in component_names:
                    if incompatible_lower in comp_name or comp_name in incompatible_lower:
                        flag_data = {
                            'formulation_plan': plan.id,
                            'component_a': excipient.name,
                            'component_b': comp_name,
                            'flag_type': 'chemical',
                            'severity': 'warning',
                            'evidence': f'Known incompatibility from excipient database: {excipient.notes}',
                        }
                        flag_serializer = CompatibilityFlagSerializer(data=flag_data)
                        if flag_serializer.is_valid():
                            flag_serializer.save()
                            new_flags.append(flag_serializer.data)

        all_flags = CompatibilityFlag.objects.filter(formulation_plan=plan)
        return Response({
            'new_flags': new_flags,
            'total_flags': CompatibilityFlagSerializer(all_flags, many=True).data,
        })


class FormulationContextView(APIView):
    def get(self, request, pk):
        try:
            plan = FormulationPlan.objects.get(pk=pk)
        except FormulationPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        return Response({
            'plan': FormulationPlanSerializer(plan).data,
            'components': FormulationComponentSerializer(plan.components.all(), many=True).data,
            'flags': CompatibilityFlagSerializer(plan.compatibility_flags.all(), many=True).data,
        })


class ExcipientSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        route = request.query_params.get('route', '').strip()
        function = request.query_params.get('function', '').strip()

        qs = Excipient.objects.all()
        if q:
            qs = qs.filter(name__icontains=q)
        if route:
            qs = qs.filter(route__icontains=route)
        if function:
            qs = qs.filter(function__icontains=function)

        return Response(ExcipientSerializer(qs[:50], many=True).data)

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import StabilityPlan, StabilityCondition, StabilityResult
from core.serializers import StabilityPlanSerializer, StabilityConditionSerializer, StabilityResultSerializer


class StabilityPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = StabilityPlanSerializer

    def get_queryset(self):
        return StabilityPlan.objects.filter(project_id=self.kwargs['pk']).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['pk'])


class StabilityPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StabilityPlan.objects.all()
    serializer_class = StabilityPlanSerializer


class StabilityConditionView(APIView):
    def get(self, request, pk):
        conditions = StabilityCondition.objects.filter(plan_id=pk)
        return Response(StabilityConditionSerializer(conditions, many=True).data)

    def post(self, request, pk):
        try:
            plan = StabilityPlan.objects.get(pk=pk)
        except StabilityPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = StabilityConditionSerializer(data={**request.data, 'plan': plan.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(plan=plan)
        return Response(serializer.data, status=201)


class StabilityResultView(APIView):
    def get(self, request, pk):
        condition_id = request.query_params.get('condition_id')
        timepoint = request.query_params.get('timepoint')

        qs = StabilityResult.objects.filter(condition__plan_id=pk)
        if condition_id:
            qs = qs.filter(condition_id=condition_id)
        if timepoint:
            qs = qs.filter(timepoint_weeks=float(timepoint))

        return Response(StabilityResultSerializer(qs, many=True).data)

    def post(self, request, pk):
        condition_id = request.data.get('condition_id')
        try:
            condition = StabilityCondition.objects.get(pk=condition_id, plan_id=pk)
        except StabilityCondition.DoesNotExist:
            return Response({'error': 'Condition not found for this plan'}, status=404)

        serializer = StabilityResultSerializer(data={**request.data, 'condition': condition.id})
        serializer.is_valid(raise_exception=True)
        serializer.save(condition=condition)
        return Response(serializer.data, status=201)


class StabilityMatrixView(APIView):
    def get(self, request, pk):
        """Return stability data organized as a matrix: conditions × timepoints."""
        try:
            plan = StabilityPlan.objects.get(pk=pk)
        except StabilityPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        conditions = StabilityCondition.objects.filter(plan=plan)
        matrix = {}
        for cond in conditions:
            results = StabilityResult.objects.filter(condition=cond).order_by('timepoint_weeks')
            matrix[cond.condition_label] = {
                'condition': StabilityConditionSerializer(cond).data,
                'timepoints': {
                    r.timepoint_weeks: StabilityResultSerializer(r).data
                    for r in results
                },
            }

        return Response({'plan_id': pk, 'matrix': matrix})


class StabilityContextView(APIView):
    def get(self, request, pk):
        try:
            plan = StabilityPlan.objects.get(pk=pk)
        except StabilityPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        conditions = StabilityCondition.objects.filter(plan=plan)
        oos_results = StabilityResult.objects.filter(condition__plan=plan, oos_flag=True)

        return Response({
            'plan': StabilityPlanSerializer(plan).data,
            'conditions': StabilityConditionSerializer(conditions, many=True).data,
            'oos_count': oos_results.count(),
            'oos_results': StabilityResultSerializer(oos_results, many=True).data,
        })

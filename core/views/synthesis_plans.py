from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import SynthesisPlan, Experiment
from core.serializers import SynthesisPlanSerializer, ExperimentSerializer


class SynthesisPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = SynthesisPlanSerializer

    def get_queryset(self):
        qs = SynthesisPlan.objects.all().order_by('-created_at')
        project_id = self.request.query_params.get('project')
        analog_id = self.request.query_params.get('analog')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if analog_id:
            qs = qs.filter(analog_candidate_id=analog_id)
        return qs

    def perform_create(self, serializer):
        analog = serializer.validated_data.get('analog_candidate')
        plan_type = serializer.validated_data.get('plan_type')
        if analog and SynthesisPlan.objects.filter(analog_candidate=analog, plan_type=plan_type).exists():
            raise ValidationError(
                {'detail': f'A {plan_type} plan for this analog already exists.'}
            )
        serializer.save()


class SynthesisPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SynthesisPlan.objects.all()
    serializer_class = SynthesisPlanSerializer


class SynthesisPlanExperimentsView(APIView):
    """Create Experiment records for each route step in the synthesis plan."""

    def post(self, request, pk):
        try:
            plan = SynthesisPlan.objects.get(pk=pk)
        except SynthesisPlan.DoesNotExist:
            return Response({'error': 'Synthesis plan not found'}, status=404)

        route_data = plan.route_data or {}
        steps = route_data.get('results', [])
        if not steps:
            return Response({'error': 'No route steps found in this plan'}, status=400)

        created = []
        for i, step in enumerate(steps):
            precursors = step.get('precursors', [])
            exp = Experiment.objects.create(
                project=plan.project,
                synthesis_plan=plan,
                title=f"Step {i + 1}: {step.get('transform', 'Unknown')}",
                experiment_type='synthesis',
                objective=(
                    f"{step.get('forward_reaction', '')}.\n\n"
                    f"Precursors: {' + '.join(precursors) if precursors else step.get('smiles', '')}.\n\n"
                    f"Target SMILES: {plan.target_smiles}"
                ),
                success_criteria=f"Successful synthesis via {step.get('transform', 'unknown transform')} with acceptable yield and purity.",
                variables=[
                    {'name': 'Precursor', 'unit': 'SMILES', 'min': '', 'max': '', 'control': p}
                    for p in precursors
                ],
                status='planned',
            )
            created.append(exp)

        plan.status = 'active'
        plan.save(update_fields=['status'])

        return Response(ExperimentSerializer(created, many=True).data, status=201)

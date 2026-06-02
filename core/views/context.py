"""
Context endpoint views — read-only aggregators for per-page AI window support.
Each view assembles all page-visible data into a single structured JSON payload.
These endpoints call no external APIs and are designed to return in <50ms.
"""

from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import (
    Project, Compound, SynthesisPlan,
    FormulationPlan, StabilityPlan, PreclinicalStudy,
)
from core.serializers import (
    ProjectSerializer, CompoundSerializer, SynthesisPlanSerializer,
    FormulationPlanSerializer, StabilityPlanSerializer, PreclinicalStudySerializer,
    ProjectPhaseSerializer, SAREntrySerializer, CompatibilityFlagSerializer,
    StabilityConditionSerializer, StabilityResultSerializer,
)


class ProjectContextView(APIView):
    def get(self, request, pk):
        try:
            project = Project.objects.prefetch_related(
                'compounds', 'experiments', 'phases', 'synthesis_plans', 'sar_entries',
            ).get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        return Response({
            'project': ProjectSerializer(project).data,
            'phases': ProjectPhaseSerializer(project.phases.all(), many=True).data,
            'compound_count': project.compounds.count(),
            'experiment_count': project.experiments.count(),
            'synthesis_plan_count': project.synthesis_plans.count(),
            'sar_entry_count': project.sar_entries.count(),
            'recent_experiments': list(
                project.experiments.order_by('-created_at')[:5].values('id', 'title', 'experiment_type', 'status')
            ),
        })


class CompoundContextView(APIView):
    def get(self, request, pk):
        try:
            compound = Compound.objects.prefetch_related('properties', 'sar_entries').get(pk=pk)
        except Compound.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        admet = compound.properties.filter(property_type='admet').order_by('-fetched_at').first()
        tox = compound.properties.filter(property_type='toxicity').order_by('-fetched_at').first()

        return Response({
            'compound': CompoundSerializer(compound).data,
            'admet': admet.data if admet else None,
            'toxicity': tox.data if tox else None,
            'sar_entries': SAREntrySerializer(compound.sar_entries.all()[:20], many=True).data,
        })


class SynthesisPlanContextView(APIView):
    def get(self, request, pk):
        try:
            plan = SynthesisPlan.objects.prefetch_related('experiments').get(pk=pk)
        except SynthesisPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        return Response({
            'plan': SynthesisPlanSerializer(plan).data,
            'experiment_count': plan.experiments.count(),
            'recent_experiments': list(
                plan.experiments.order_by('-created_at')[:5].values('id', 'title', 'status')
            ),
        })


class FormulationPlanContextView(APIView):
    def get(self, request, pk):
        try:
            plan = FormulationPlan.objects.prefetch_related('components', 'compatibility_flags').get(pk=pk)
        except FormulationPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        return Response({
            'plan': FormulationPlanSerializer(plan).data,
            'components': list(plan.components.values('name', 'component_type', 'concentration', 'unit')),
            'flag_count': plan.compatibility_flags.count(),
            'critical_flags': CompatibilityFlagSerializer(
                plan.compatibility_flags.filter(severity='critical'), many=True
            ).data,
        })


class StabilityPlanContextView(APIView):
    def get(self, request, pk):
        try:
            plan = StabilityPlan.objects.prefetch_related('conditions').get(pk=pk)
        except StabilityPlan.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        from core.models import StabilityResult
        oos_results = StabilityResult.objects.filter(condition__plan=plan, oos_flag=True)

        return Response({
            'plan': StabilityPlanSerializer(plan).data,
            'conditions': StabilityConditionSerializer(plan.conditions.all(), many=True).data,
            'oos_count': oos_results.count(),
            'oos_results': StabilityResultSerializer(oos_results[:10], many=True).data,
        })


class PreclinicalStudyContextView(APIView):
    def get(self, request, pk):
        try:
            study = PreclinicalStudy.objects.get(pk=pk)
        except PreclinicalStudy.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        from core.models import CompoundProperty
        project_compounds = Compound.objects.filter(project=study.project)
        admet_data = {}
        for c in project_compounds:
            admet = CompoundProperty.objects.filter(compound=c, property_type='admet').order_by('-fetched_at').first()
            if admet:
                admet_data[c.name] = admet.data

        return Response({
            'study': PreclinicalStudySerializer(study).data,
            'admet_data': admet_data,
        })

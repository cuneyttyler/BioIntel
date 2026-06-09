import json

from django.http import StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import AIPlan, AIPlanDiscussion, AIPlanStep, Project
from core.serializers import AIPlanDiscussionSerializer, AIPlanSerializer, AIPlanStepSerializer
from core.services import ai_plan as ai_plan_service
from core.services import claude_client


class ProjectAIPlanView(APIView):
    """GET or POST /api/projects/<id>/ai-plan/ — retrieve or create plan for a project."""

    def get(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        try:
            plan = project.ai_plan
        except AIPlan.DoesNotExist:
            return Response({'error': 'No AI plan for this project'}, status=404)

        return Response(AIPlanSerializer(plan).data)

    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        if hasattr(project, 'ai_plan'):
            return Response({'error': 'Plan already exists'}, status=400)

        plan = AIPlan.objects.create(
            project=project,
            molecule_type=request.data.get('molecule_type', project.molecule_type),
            disease_description=request.data.get('disease_description', project.description),
            constraints=request.data.get('constraints', {}),
        )
        project.mode = 'ai_driven'
        project.save(update_fields=['mode'])

        steps = ai_plan_service.create_plan_steps(plan.id, plan.molecule_type)
        plan.step_count = len(steps)
        plan.save(update_fields=['step_count'])

        ai_plan_service.advance_plan(plan.id)

        return Response(AIPlanSerializer(plan).data, status=201)


class AIPlanDetailView(generics.RetrieveUpdateAPIView):
    queryset = AIPlan.objects.all()
    serializer_class = AIPlanSerializer


class AIPlanGenerateView(APIView):
    """POST /api/ai-plans/<pk>/generate/ — SSE: generate/regenerate the full plan."""

    def post(self, request, pk):
        try:
            plan = AIPlan.objects.select_related('project').get(pk=pk)
        except AIPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=404)

        def event_stream():
            yield from claude_client.stream_plan_generation(plan.project_id, plan.id)

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


class AIPlanStepDetailView(generics.RetrieveUpdateAPIView):
    queryset = AIPlanStep.objects.all()
    serializer_class = AIPlanStepSerializer


class AIPlanStepApproveView(APIView):
    """POST /api/ai-plan-steps/<pk>/approve/"""

    def post(self, request, pk):
        try:
            step = ai_plan_service.approve_step(pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)
        return Response(AIPlanStepSerializer(step).data)


class AIPlanStepRejectView(APIView):
    """POST /api/ai-plan-steps/<pk>/reject/"""

    def post(self, request, pk):
        feedback = request.data.get('feedback', '')
        try:
            step = ai_plan_service.reject_step(pk, feedback)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)
        return Response(AIPlanStepSerializer(step).data)


class AIPlanStepSkipView(APIView):
    """POST /api/ai-plan-steps/<pk>/skip/"""

    def post(self, request, pk):
        try:
            step = ai_plan_service.skip_step(pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)
        return Response(AIPlanStepSerializer(step).data)


class AIPlanStepRecommendView(APIView):
    """POST /api/ai-plan-steps/<pk>/recommend/ — SSE: generate/regenerate step recommendation."""

    def post(self, request, pk):
        try:
            step = AIPlanStep.objects.select_related('plan').get(pk=pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)

        step.status = 'in_progress'
        step.save(update_fields=['status', 'updated_at'])

        def event_stream():
            yield from claude_client.stream_step_recommendation(step.plan_id, step.id)

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


class AIPlanStepDiscussView(APIView):
    """POST /api/ai-plan-steps/<pk>/discuss/ — SSE: per-step discussion."""

    def post(self, request, pk):
        try:
            step = AIPlanStep.objects.select_related('plan').get(pk=pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)

        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'message required'}, status=400)

        def event_stream():
            yield from claude_client.stream_step_discussion(step.plan_id, step.id, message)

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


class AIPlanStepAnalyzeResultsView(APIView):
    """POST /api/ai-plan-steps/<pk>/analyze-results/ — SSE: post-experiment analysis."""

    def post(self, request, pk):
        try:
            step = AIPlanStep.objects.select_related('plan').get(pk=pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)

        experiment_results = request.data.get('results', {})

        def event_stream():
            yield from claude_client.stream_result_analysis(step.plan_id, step.id, experiment_results)

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


class AIPlanStepGoBackView(APIView):
    """POST /api/ai-plan-steps/<pk>/go-back/ — branch plan back to target step."""

    def post(self, request, pk):
        try:
            step = AIPlanStep.objects.select_related('plan').get(pk=pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)

        target_step_number = request.data.get('target_step_number')
        if target_step_number is None:
            return Response({'error': 'target_step_number required'}, status=400)

        new_steps = ai_plan_service.go_back_to_step(step.plan_id, int(target_step_number))
        return Response({'new_steps': AIPlanStepSerializer(new_steps, many=True).data})


class AIPlanDiscussionListView(APIView):
    """GET /api/ai-plan-steps/<pk>/discussions/ — list step discussion messages."""

    def get(self, request, pk):
        try:
            step = AIPlanStep.objects.get(pk=pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)

        msgs = AIPlanDiscussion.objects.filter(step=step).order_by('created_at')
        return Response(AIPlanDiscussionSerializer(msgs, many=True).data)


class AIPlanCompressContextView(APIView):
    """POST /api/ai-plans/<pk>/compress-context/ — manually trigger context compression."""

    def post(self, request, pk):
        try:
            AIPlan.objects.get(pk=pk)
        except AIPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=404)

        ai_plan_service.compress_plan_context(pk)
        return Response({'status': 'compressed'})


class AIPlanStepExecuteActionView(APIView):
    """POST /api/ai-plan-steps/<pk>/execute-action/ — apply a suggested action to BioIntel data."""

    ACTION_HANDLERS = {
        'add_drug_investigation',
        'add_analog_candidate',
        'add_sar_entry',
        'add_analytical_method',
        'add_preclinical_study',
        'add_formulation_plan',
        'add_stability_plan',
        'update_project_description',
    }

    def post(self, request, pk):
        try:
            step = AIPlanStep.objects.select_related('plan__project').get(pk=pk)
        except AIPlanStep.DoesNotExist:
            return Response({'error': 'Step not found'}, status=404)

        action_id = request.data.get('action_id', '')
        action_type = request.data.get('action_type', '')
        data = request.data.get('data', {})

        if action_type not in self.ACTION_HANDLERS:
            return Response({'error': f'Unknown action_type: {action_type}'}, status=400)

        project = step.plan.project
        result = self._execute(action_type, data, project, step)

        # Mark action as applied on the step
        actions = list(step.suggested_actions or [])
        for a in actions:
            if a.get('id') == action_id:
                a['applied'] = True
        step.suggested_actions = actions
        step.save(update_fields=['suggested_actions', 'updated_at'])

        return Response({'status': 'applied', 'result': result})

    def _execute(self, action_type, data, project, step):
        from core.models import (
            DrugInvestigation, AnalogCandidate, SAREntry,
            AnalyticalMethod, PreclinicalStudy, FormulationPlan, StabilityPlan,
        )

        if action_type == 'add_drug_investigation':
            inv = DrugInvestigation.objects.create(
                project=project,
                name=data.get('name', 'Reference compound'),
                chembl_id=data.get('chembl_id', ''),
                smiles=data.get('smiles', ''),
                disease_name=data.get('disease_name', ''),
                notes=data.get('notes', ''),
            )
            return {'id': inv.id, 'name': inv.name}

        elif action_type == 'add_analog_candidate':
            inv = DrugInvestigation.objects.filter(project=project).first()
            if not inv:
                inv = DrugInvestigation.objects.create(
                    project=project,
                    name='Auto-created for AI plan',
                    chembl_id='',
                )
            candidate = AnalogCandidate.objects.create(
                investigation=inv,
                project=project,
                smiles=data.get('smiles', ''),
                similarity_score=data.get('similarity_score', 0.0),
                patent_status=data.get('patent_status', 'unknown'),
                notes=data.get('notes', ''),
            )
            return {'id': candidate.id}

        elif action_type == 'add_sar_entry':
            entry = SAREntry.objects.create(
                project=project,
                r_group=data.get('r_group', ''),
                activity_type=data.get('activity_type', 'IC50'),
                activity_value=data.get('activity_value'),
                activity_unit=data.get('activity_unit', 'nM'),
                notes=data.get('notes', ''),
            )
            return {'id': entry.id}

        elif action_type == 'add_analytical_method':
            method = AnalyticalMethod.objects.create(
                project=project,
                method_name=data.get('method_name', 'Method'),
                method_type=data.get('method_type', 'other'),
                analyte=data.get('analyte', ''),
                validation_status=data.get('validation_status', 'not_started'),
            )
            return {'id': method.id, 'method_name': method.method_name}

        elif action_type == 'add_preclinical_study':
            study = PreclinicalStudy.objects.create(
                project=project,
                study_type=data.get('study_type', 'toxicology'),
                species=data.get('species', ''),
                dose_route=data.get('dose_route', ''),
                status=data.get('status', 'planned'),
            )
            return {'id': study.id, 'study_type': study.study_type}

        elif action_type == 'add_formulation_plan':
            fp = FormulationPlan.objects.create(
                project=project,
                dosage_form=data.get('dosage_form', 'tablet'),
                route_of_administration=data.get('route_of_administration', 'oral'),
                status=data.get('status', 'draft'),
                rationale=data.get('rationale', ''),
            )
            return {'id': fp.id, 'dosage_form': fp.dosage_form}

        elif action_type == 'add_stability_plan':
            sp = StabilityPlan.objects.create(
                project=project,
                material_type=data.get('material_type', 'drug_substance'),
                intended_storage_condition=data.get('intended_storage_condition', ''),
                status=data.get('status', 'planned'),
            )
            return {'id': sp.id}

        elif action_type == 'update_project_description':
            project.description = data.get('description', project.description)
            project.save(update_fields=['description'])
            return {'updated': True}

        return {}

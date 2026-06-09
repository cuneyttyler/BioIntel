"""
AI Plan state machine, context management, and helper functions.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

AI_PLAN_CONTEXT_WINDOW_MESSAGES = 10
COMPRESSION_THRESHOLD = 100


def get_plan_or_404(plan_id: int):
    from core.models import AIPlan
    return AIPlan.objects.select_related('project').get(id=plan_id)


def get_step_or_404(step_id: int):
    from core.models import AIPlanStep
    return AIPlanStep.objects.select_related('plan__project').get(id=step_id)


# ─── State machine ────────────────────────────────────────────────────────────

def advance_plan(plan_id: int) -> 'AIPlanStep | None':
    """Activate the next pending step. Returns the newly activated step or None if plan is done."""
    from core.models import AIPlan, AIPlanStep

    plan = AIPlan.objects.get(id=plan_id)
    next_step = AIPlanStep.objects.filter(plan=plan, status='pending').order_by('step_number').first()

    if next_step is None:
        plan.status = 'completed'
        plan.current_step_number = None
        plan.save(update_fields=['status', 'current_step_number', 'updated_at'])
        return None

    next_step.status = 'in_progress'
    next_step.save(update_fields=['status', 'updated_at'])
    plan.current_step_number = next_step.step_number
    plan.save(update_fields=['current_step_number', 'updated_at'])
    return next_step


def approve_step(step_id: int) -> 'AIPlanStep':
    """Mark step as completed, advance to next step."""
    from core.models import AIPlanStep

    step = AIPlanStep.objects.select_related('plan').get(id=step_id)
    step.status = 'completed'
    step.save(update_fields=['status', 'updated_at'])
    advance_plan(step.plan_id)
    return step


def reject_step(step_id: int, feedback: str = '') -> 'AIPlanStep':
    """Mark step as revision_needed with scientist feedback."""
    from core.models import AIPlanStep

    step = AIPlanStep.objects.get(id=step_id)
    step.status = 'revision_needed'
    step.scientist_feedback = feedback
    step.save(update_fields=['status', 'scientist_feedback', 'updated_at'])
    return step


def skip_step(step_id: int) -> 'AIPlanStep':
    """Skip a step and advance to the next."""
    from core.models import AIPlanStep

    step = AIPlanStep.objects.select_related('plan').get(id=step_id)
    step.status = 'skipped'
    step.save(update_fields=['status', 'updated_at'])
    advance_plan(step.plan_id)
    return step


def go_back_to_step(plan_id: int, target_step_number: int) -> list['AIPlanStep']:
    """
    Branch the plan back to target_step_number.

    All steps from target_step_number to the current step are set to 'abandoned'.
    Fresh AIPlanStep records are created starting from target_step_number with
    status='pending', preserving the original title/phase/description as templates.
    Returns the list of newly created steps.
    """
    from core.models import AIPlan, AIPlanStep

    plan = AIPlan.objects.get(id=plan_id)
    current_number = plan.current_step_number or 0

    steps_to_abandon = AIPlanStep.objects.filter(
        plan=plan,
        step_number__gte=target_step_number,
        step_number__lte=current_number,
    ).exclude(status='abandoned')

    # Copy template info before abandoning
    templates = [
        {
            'step_number': s.step_number,
            'phase': s.phase,
            'title': s.title,
            'description': s.description,
            'experiment_required': s.experiment_required,
        }
        for s in steps_to_abandon.order_by('step_number')
    ]

    steps_to_abandon.update(status='abandoned')

    # Create fresh steps
    new_steps = []
    for tmpl in templates:
        new_step = AIPlanStep.objects.create(
            plan=plan,
            status='pending',
            ai_recommendation={},
            ai_reasoning='',
            scientist_feedback='',
            entities_created=[],
            rag_sources=[],
            **tmpl,
        )
        new_steps.append(new_step)

    plan.current_step_number = target_step_number
    plan.status = 'active'
    plan.save(update_fields=['current_step_number', 'status', 'updated_at'])

    # Activate the first new step
    if new_steps:
        new_steps[0].status = 'in_progress'
        new_steps[0].save(update_fields=['status', 'updated_at'])

    return new_steps


# ─── Context management ───────────────────────────────────────────────────────

def build_plan_messages(
    plan_id: int,
    step_id: int | None = None,
    new_message: str | None = None,
) -> list[dict]:
    """
    Build the messages list for an AI call on a plan/step discussion.

    Strategy:
    1. If plan.conversation_context has a summary, prepend it as a user+assistant pair.
    2. Append the last AI_PLAN_CONTEXT_WINDOW_MESSAGES messages from the discussion.
    3. Append new_message as a user message if provided.
    """
    from core.models import AIPlan, AIPlanDiscussion

    plan = AIPlan.objects.get(id=plan_id)
    messages = []

    ctx = plan.conversation_context
    if ctx and ctx.get('summary'):
        messages.append({
            'role': 'user',
            'content': f"[Context summary from earlier in this session]\n{ctx['summary']}",
        })
        messages.append({
            'role': 'assistant',
            'content': 'Understood. I have the context of our previous discussion.',
        })

    qs = AIPlanDiscussion.objects.filter(plan_id=plan_id)
    if step_id is not None:
        qs = qs.filter(step_id=step_id)

    recent = list(qs.order_by('-created_at')[:AI_PLAN_CONTEXT_WINDOW_MESSAGES])
    recent.reverse()

    for msg in recent:
        messages.append({
            'role': 'user' if msg.role == 'scientist' else 'assistant',
            'content': msg.content,
        })

    if new_message:
        messages.append({'role': 'user', 'content': new_message})

    return messages


def should_compress(plan_id: int) -> bool:
    from core.models import AIPlanDiscussion
    count = AIPlanDiscussion.objects.filter(plan_id=plan_id).count()
    return count >= COMPRESSION_THRESHOLD


def compress_plan_context(plan_id: int) -> None:
    """Summarize all plan discussions and store in AIPlan.conversation_context."""
    from core.models import AIPlan, AIPlanDiscussion
    from core.services.claude_client import generate_once

    messages = AIPlanDiscussion.objects.filter(plan_id=plan_id).order_by('created_at')
    message_count = messages.count()

    formatted = []
    for msg in messages:
        step_label = f" (Step {msg.step.step_number})" if msg.step_id else ""
        formatted.append(f"[{msg.role.upper()}{step_label}]: {msg.content}")

    conversation_text = '\n\n'.join(formatted)

    summary = generate_once(
        system=(
            "You are summarizing a drug development planning conversation between a scientist "
            "and an AI assistant. Produce a concise structured summary covering: "
            "(1) project goals and constraints, "
            "(2) decisions made at each completed step, "
            "(3) key findings and recommendations accepted by the scientist, "
            "(4) any plan branches or revisions requested, "
            "(5) current state of the plan. "
            "Be specific and preserve scientific details (compound names, SMILES, thresholds, etc.)."
        ),
        user_content=f"Please summarize the following drug development planning conversation:\n\n{conversation_text}",
    )

    plan = AIPlan.objects.get(id=plan_id)
    plan.conversation_context = {
        'summary': summary,
        'compressed_at': datetime.now(timezone.utc).isoformat(),
        'message_count': message_count,
    }
    plan.save(update_fields=['conversation_context', 'updated_at'])
    logger.info(f"Compressed context for plan {plan_id}: {message_count} messages summarized")


def save_discussion_message(
    plan_id: int,
    step_id: int | None,
    role: str,
    content: str,
    tool_calls: list | None = None,
    sources: list | None = None,
) -> 'AIPlanDiscussion':
    from core.models import AIPlanDiscussion

    msg = AIPlanDiscussion.objects.create(
        plan_id=plan_id,
        step_id=step_id,
        role=role,
        content=content,
        tool_calls=tool_calls or [],
        sources=sources or [],
    )

    if should_compress(plan_id):
        try:
            compress_plan_context(plan_id)
        except Exception as exc:
            logger.warning(f"Context compression failed for plan {plan_id}: {exc}")

    return msg


# ─── Step template factories ──────────────────────────────────────────────────

SMALL_MOLECULE_STEPS = [
    (1, 'discovery', 'Disease & Target Identification'),
    (2, 'discovery', 'Reference Drug / Target Structure Selection'),
    (3, 'discovery', 'Patent Landscape & Freedom-to-Operate'),
    (4, 'discovery', 'Virtual Screening / Analog Search'),
    (5, 'discovery', 'ADMET Profiling & Candidate Shortlisting'),
    (6, 'lead_optimization', 'Lead Optimization Objectives (SAR Goals)'),
    (7, 'lead_optimization', 'Candidate Selection Gate'),
    (8, 'drug_substance', 'Synthesis Route Planning'),
    (9, 'drug_substance', 'Salt / Polymorph Form Selection'),
    (10, 'drug_product', 'Drug Product Target Definition'),
    (11, 'drug_product', 'Excipient Selection & Compatibility'),
    (12, 'drug_product', 'Stability Study Design'),
    (13, 'analytical', 'Analytical Method Development Plan'),
    (14, 'preclinical', 'Preclinical Study Package Design'),
    (15, 'regulatory', 'IND Package Readiness Assessment'),
]

BIOLOGIC_STEPS = [
    (1, 'discovery', 'Antigen / Target Identification'),
    (2, 'discovery', 'Biologic Modality Selection'),
    (3, 'discovery', 'Sequence Design / Humanization'),
    (4, 'discovery', 'Developability Assessment'),
    (5, 'drug_substance', 'Expression System Selection & Transfection Strategy'),
    (6, 'drug_substance', 'Cell Line Development: Clone Selection & Stability'),
    (7, 'drug_substance', 'Upstream Process Development'),
    (8, 'drug_substance', 'Downstream Purification Train Design'),
    (9, 'analytical', 'Drug Substance Characterization Plan'),
    (10, 'drug_product', 'Formulation Screening'),
    (11, 'drug_product', 'Container Closure Selection'),
    (12, 'drug_product', 'Lyophilization Design'),
    (13, 'drug_product', 'Stability Study Design (ICH Q5C)'),
    (14, 'preclinical', 'Preclinical Safety Package Design'),
    (15, 'regulatory', 'BLA Readiness Assessment'),
]


def create_plan_steps(plan_id: int, molecule_type: str) -> list['AIPlanStep']:
    """Create the default step set for a new AI plan."""
    from core.models import AIPlanStep

    template = BIOLOGIC_STEPS if molecule_type == 'biologic' else SMALL_MOLECULE_STEPS
    steps = []
    for step_num, phase, title in template:
        step = AIPlanStep.objects.create(
            plan_id=plan_id,
            step_number=step_num,
            phase=phase,
            title=title,
            status='pending',
        )
        steps.append(step)
    return steps

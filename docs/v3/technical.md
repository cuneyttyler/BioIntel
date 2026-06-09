# BioIntel — Technical Specification v3

## Overview

BioIntel v3 adds an AI-Driven project mode, a per-page AI panel, a RAG-backed document corpus, and a full biologics development pathway on top of the v2 foundation. This document covers all new technical additions. Existing v2 architecture (models, views, services, patterns) is documented in `v2/technical.md` and is unchanged in v3 unless explicitly noted here.

---

## Stack

### Unchanged from v2
- **Framework**: Django 6.0.5 + Django REST Framework 3.17.1
- **Database**: SQLite (dev) → PostgreSQL (production)
- **Frontend**: Vue 3.5 + Pinia + Vue Router 4 + Vite + Axios
- **AI**: Anthropic SDK (claude-sonnet-4-6)
- **Static files**: WhiteNoise
- **WSGI**: Gunicorn (production)

### New in v3

| Component | Package | Purpose |
|---|---|---|
| Embeddings | `sentence-transformers>=2.7.0` | Local embedding model (all-MiniLM-L6-v2, 384 dims, free, no API cost) |
| PDF parsing | `pdfplumber>=0.11.0` | Text extraction from uploaded and playbook PDFs |
| DOCX parsing | `python-docx>=1.1.0` | Text extraction from .docx uploads |
| Numpy | `numpy>=1.26.0` | Cosine similarity computation for RAG retrieval (dev) |
| pgvector | `pgvector>=0.3.0` | Vector column support (production PostgreSQL only; not required in dev) |

Add to `requirements.txt`:
```
sentence-transformers>=2.7.0
pdfplumber>=0.11.0
python-docx>=1.1.0
numpy>=1.26.0
pgvector>=0.3.0
```

### New Settings (`backend/settings.py`)

```python
# v3 additions
RAG_CORPUS_DIR = BASE_DIR / 'rag_corpus'          # Pharmaceutical playbook PDFs (git-ignored)
MEDIA_ROOT = BASE_DIR / 'media'                    # User-uploaded documents
MEDIA_URL = '/media/'
RAG_CHUNK_SIZE = 500                               # tokens per chunk
RAG_CHUNK_OVERLAP = 50                             # overlap tokens between chunks
RAG_TOP_K = 5                                      # chunks returned per query
AI_PLAN_COMPRESSION_THRESHOLD = 100               # messages before context compression
AI_PLAN_CONTEXT_WINDOW_MESSAGES = 10              # messages kept after compression
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'             # sentence-transformers model name
```

---

## New Database Schema

All migrations are additive. No v2 table is modified except `Project` and `Compound` (new nullable fields only). All existing v2 projects default to `mode=manual, molecule_type=small_molecule` — no data loss.

### Migration `0013_v3_project_fields.py`

```python
# Adds mode and molecule_type to Project; sequence to Compound

migrations.AddField(
    model_name='project',
    name='mode',
    field=models.CharField(max_length=20, default='manual',
                           choices=[('manual','Manual'),('ai_driven','AI-Driven')]),
),
migrations.AddField(
    model_name='project',
    name='molecule_type',
    field=models.CharField(max_length=20, default='small_molecule',
                           choices=[('small_molecule','Small Molecule'),
                                    ('biologic','Biologic'),
                                    ('undetermined','Undetermined')]),
),
migrations.AddField(
    model_name='compound',
    name='sequence',
    field=models.TextField(null=True, blank=True),
),
```

### Migration `0014_ai_plan_tables.py`

```python
# Creates ai_plans, ai_plan_steps, ai_plan_discussions

class AIPlan(models.Model):
    project = models.OneToOneField('Project', on_delete=models.CASCADE,
                                   related_name='ai_plan')
    status = models.CharField(max_length=20, default='draft',
        choices=[('draft','Draft'),('active','Active'),('paused','Paused'),
                 ('completed','Completed'),('archived','Archived')])
    molecule_type = models.CharField(max_length=20, default='small_molecule')
    disease_description = models.TextField(blank=True)
    constraints = models.JSONField(default=dict)
    conversation_context = models.JSONField(default=dict)  # compressed summary
    step_count = models.IntegerField(default=0)
    current_step_number = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AIPlanStep(models.Model):
    STATUSES = [
        ('pending','Pending'), ('in_progress','In Progress'),
        ('awaiting_approval','Awaiting Approval'), ('approved','Approved'),
        ('revision_needed','Revision Needed'), ('completed','Completed'),
        ('skipped','Skipped'), ('abandoned','Abandoned'),
    ]
    plan = models.ForeignKey(AIPlan, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField()
    phase = models.CharField(max_length=30)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, default='pending', choices=STATUSES)
    ai_recommendation = models.JSONField(default=dict)
    ai_reasoning = models.TextField(blank=True)
    scientist_feedback = models.TextField(blank=True)
    entities_created = models.JSONField(default=list)
    experiment_required = models.BooleanField(default=False)
    experiment = models.ForeignKey('Experiment', null=True, blank=True,
                                   on_delete=models.SET_NULL)
    rag_sources = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['step_number']
        unique_together = [('plan', 'step_number')]

class AIPlanDiscussion(models.Model):
    plan = models.ForeignKey(AIPlan, on_delete=models.CASCADE,
                             related_name='discussions')
    step = models.ForeignKey(AIPlanStep, null=True, blank=True,
                             on_delete=models.CASCADE, related_name='discussions')
    role = models.CharField(max_length=10,
                            choices=[('ai','AI'),('scientist','Scientist')])
    content = models.TextField()
    tool_calls = models.JSONField(default=list)
    sources = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
```

### Migration `0015_rag_tables.py`

```python
class RagDocument(models.Model):
    name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=30, choices=[
        ('ich_guideline','ICH Guideline'),('academic_paper','Academic Paper'),
        ('lab_report','Lab Report'),('regulatory_submission','Regulatory Submission'),
        ('competitor_analysis','Competitor Analysis'),('clinical_data','Clinical Data'),
        ('protocol','Protocol'),('other','Other'),
    ])
    molecule_type = models.CharField(max_length=20, default='both')
    phase_relevance = models.JSONField(default=list)  # list of phase names
    file_path = models.CharField(max_length=500)
    page_count = models.IntegerField(null=True, blank=True)
    ingestion_status = models.CharField(max_length=20, default='pending',
        choices=[('pending','Pending'),('processing','Processing'),
                 ('ready','Ready'),('failed','Failed')])
    ingestion_error = models.TextField(null=True, blank=True)
    project = models.ForeignKey('Project', null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='rag_documents')
    uploaded_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class RagChunk(models.Model):
    document = models.ForeignKey(RagDocument, on_delete=models.CASCADE,
                                  related_name='chunks')
    chunk_index = models.IntegerField()
    chunk_text = models.TextField()
    # In dev (SQLite): stored as JSON float array
    # In production (PostgreSQL + pgvector): migrate to vector(384) column
    embedding = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chunk_index']
        unique_together = [('document', 'chunk_index')]
```

### Migration `0016_biologics_tables.py`

```python
class CellLineDevelopment(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                                 related_name='cell_line_developments')
    expression_system = models.CharField(max_length=30, choices=[
        ('cho','CHO'),('hek293','HEK293'),('ecoli','E. coli'),
        ('yeast','Yeast (Pichia)'),('insect','Insect (Sf9/Hi5)'),('other','Other'),
    ])
    vector_name = models.CharField(max_length=255, blank=True)
    selection_marker = models.CharField(max_length=100, blank=True)
    cloning_method = models.CharField(max_length=50, choices=[
        ('limiting_dilution','Limiting Dilution'),('facs','FACS Sorting'),
        ('clonepix','ClonePix'),('other','Other'),
    ], blank=True)
    productivity_target_mg_l = models.FloatField(null=True, blank=True)
    aggregation_limit_pct = models.FloatField(null=True, blank=True)
    purity_target_pct = models.FloatField(null=True, blank=True)
    stability_plan = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)

class BioprocessDevelopment(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                                 related_name='bioprocess_developments')
    scale = models.CharField(max_length=30, choices=[
        ('microscale','Microscale (ambr)'),('bench','Bench (2L)'),
        ('pilot','Pilot (50L)'),('manufacturing','Manufacturing (500L+)'),
    ])
    mode = models.CharField(max_length=20, choices=[
        ('batch','Batch'),('fed_batch','Fed-batch'),('perfusion','Perfusion'),
    ])
    vessel_type = models.CharField(max_length=50, blank=True)
    cpps = models.JSONField(default=dict)   # {ph, do, temp, agitation, co2, osmolality, feed}
    cqas = models.JSONField(default=dict)   # {titer, aggregation, charge_variants, glycan}
    media_name = models.CharField(max_length=255, blank=True)
    feed_strategy = models.TextField(blank=True)
    pat_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)

class DownstreamPurification(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                                 related_name='downstream_purifications')
    steps = models.JSONField(default=list)
    # Each step: {order, unit_op, purpose, entry_criteria, conditions,
    #             pool_criteria, expected_yield_pct}
    overall_yield_target_pct = models.FloatField(null=True, blank=True)
    hcp_target_ppm = models.FloatField(null=True, blank=True)
    dna_target_ng_mg = models.FloatField(null=True, blank=True)
    endotoxin_target_eu_mg = models.FloatField(null=True, blank=True)
    monomer_target_pct = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)

class BiologicsFormulation(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                                 related_name='biologics_formulations')
    target_concentration_mg_ml = models.FloatField(null=True, blank=True)
    route = models.CharField(max_length=30, choices=[
        ('sc','Subcutaneous (SC)'),('iv','Intravenous (IV)'),
        ('im','Intramuscular (IM)'),('intravitreal','Intravitreal'),
    ])
    volume_per_dose_ml = models.FloatField(null=True, blank=True)
    presentation = models.CharField(max_length=30, choices=[
        ('liquid_vial','Liquid — Vial'),('liquid_pfs','Liquid — Prefilled Syringe'),
        ('lyophilized_vial','Lyophilized — Vial'),
    ])
    buffer_name = models.CharField(max_length=100, blank=True)
    buffer_ph = models.FloatField(null=True, blank=True)
    stabilizer_name = models.CharField(max_length=255, blank=True)
    stabilizer_pct = models.FloatField(null=True, blank=True)
    surfactant_name = models.CharField(max_length=100, blank=True)
    surfactant_pct = models.FloatField(null=True, blank=True)
    container_type = models.CharField(max_length=50, blank=True)
    lyo_cycle = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

class BiologicsCharacterizationMethod(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE,
                                 related_name='biologics_char_methods')
    method_type = models.CharField(max_length=30, choices=[
        ('sec_hplc','SEC-HPLC'),('icief','icIEF'),('glycan','Glycan Analysis'),
        ('hcp_elisa','HCP ELISA'),('residual_dna','Residual DNA (qPCR)'),
        ('bioassay','Bioassay'),('spr','SPR'),('cd','CD Spectroscopy'),
        ('dsc_nandof','DSC / nano-DSF'),('peptide_mapping','Peptide Mapping'),
        ('ce_sds','CE-SDS'),('other','Other'),
    ])
    purpose = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default='in_development')
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## RAG Pipeline

### Overview

The RAG (Retrieval-Augmented Generation) pipeline has two components:
1. **Ingest**: converts documents to text chunks → embeddings → stored in `RagChunk`
2. **Retrieve**: at each AI call, encodes the query, finds the most relevant chunks via cosine similarity, injects them into the AI context

### Embedding Model

**Model**: `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- License: Apache 2.0 (free for commercial use)
- Size: ~22 MB (downloaded once, cached locally)
- Inference: CPU-based (fast enough for the corpus size; no GPU required)
- Load once at startup via `SentenceTransformerService` singleton

```python
# core/services/rag.py

from sentence_transformers import SentenceTransformer
import numpy as np
from core.models import RagChunk, RagDocument

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def embed(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()

def retrieve(query: str, phase: str = None, molecule_type: str = None,
             project_id: int = None, top_k: int = None) -> list[dict]:
    """
    Returns the top_k most relevant chunks for a query.
    Filters by phase_relevance and molecule_type if provided.
    Includes global (project=null) + project-specific docs.
    """
    top_k = top_k or settings.RAG_TOP_K
    query_vec = np.array(embed(query))

    # Build queryset
    qs = RagChunk.objects.filter(
        document__ingestion_status='ready'
    ).select_related('document')

    if molecule_type and molecule_type != 'undetermined':
        qs = qs.filter(
            document__molecule_type__in=[molecule_type, 'both']
        )
    if phase:
        qs = qs.filter(document__phase_relevance__contains=phase)

    # Scope: global docs + project-specific docs
    if project_id:
        from django.db.models import Q
        qs = qs.filter(Q(document__project__isnull=True) |
                       Q(document__project_id=project_id))
    else:
        qs = qs.filter(document__project__isnull=True)

    # Load embeddings and compute cosine similarity
    chunks = list(qs.values('id', 'chunk_text', 'embedding',
                            'document__name', 'chunk_index'))
    if not chunks:
        return []

    embeddings = np.array([c['embedding'] for c in chunks])
    scores = embeddings @ query_vec  # dot product (vectors are normalized)
    top_indices = np.argsort(scores)[::-1][:top_k]

    return [
        {
            'document': chunks[i]['document__name'],
            'chunk_index': chunks[i]['chunk_index'],
            'text': chunks[i]['chunk_text'],
            'score': float(scores[i]),
        }
        for i in top_indices
    ]
```

### Ingest Pipeline

**Management command**: `python manage.py ingest_rag_corpus`

```python
# core/management/commands/ingest_rag_corpus.py

import pdfplumber
import docx
from pathlib import Path
from core.models import RagDocument, RagChunk
from core.services.rag import embed

class Command(BaseCommand):
    help = 'Ingest documents from a directory into the RAG pipeline'

    def add_arguments(self, parser):
        parser.add_argument('--corpus-dir', type=str,
                            default=str(settings.RAG_CORPUS_DIR))
        parser.add_argument('--project-id', type=int, default=None)
        parser.add_argument('--document-type', type=str, default='ich_guideline')

    def handle(self, *args, **options):
        corpus_dir = Path(options['corpus_dir'])
        for file_path in corpus_dir.rglob('*'):
            if file_path.suffix.lower() not in ('.pdf', '.docx', '.txt'):
                continue
            self._ingest_file(file_path, options)

    def _ingest_file(self, path, options):
        doc, created = RagDocument.objects.get_or_create(
            file_path=str(path.relative_to(settings.BASE_DIR)),
            defaults={
                'name': path.stem,
                'document_type': options['document_type'],
                'molecule_type': 'both',
                'phase_relevance': [],
                'ingestion_status': 'pending',
                'project_id': options.get('project_id'),
            }
        )
        doc.ingestion_status = 'processing'
        doc.save()
        try:
            text = extract_text(path)
            chunks = chunk_text(text)
            doc.page_count = get_page_count(path)
            RagChunk.objects.filter(document=doc).delete()
            for i, chunk in enumerate(chunks):
                RagChunk.objects.create(
                    document=doc,
                    chunk_index=i,
                    chunk_text=chunk,
                    embedding=embed(chunk),
                )
            doc.ingestion_status = 'ready'
            doc.ingestion_error = None
        except Exception as e:
            doc.ingestion_status = 'failed'
            doc.ingestion_error = str(e)
        doc.save()

def extract_text(path: Path) -> str:
    if path.suffix == '.pdf':
        with pdfplumber.open(path) as pdf:
            return '\n'.join(page.extract_text() or '' for page in pdf.pages)
    elif path.suffix == '.docx':
        doc = docx.Document(str(path))
        return '\n'.join(p.text for p in doc.paragraphs)
    else:  # .txt
        return path.read_text(encoding='utf-8')

def chunk_text(text: str, size: int = None, overlap: int = None) -> list[str]:
    size = size or settings.RAG_CHUNK_SIZE
    overlap = overlap or settings.RAG_CHUNK_OVERLAP
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(' '.join(words[start:end]))
        start += size - overlap
    return [c for c in chunks if len(c.strip()) > 50]
```

**On-demand ingest** (triggered when scientist uploads via Document Portal):

```python
# core/views/documents.py

class DocumentIngestView(APIView):
    def post(self, request, pk):
        doc = get_object_or_404(RagDocument, pk=pk)
        doc.ingestion_status = 'processing'
        doc.save()
        # Run synchronously (acceptable for <50MB files; replace with Celery in prod)
        ingest_document(doc)
        return Response({'status': doc.ingestion_status})
```

### Production Upgrade: pgvector

In production (PostgreSQL), replace the `embedding` JSONField with a proper vector column:

```python
# Migration 0015_rag_pgvector.py (production only)
from pgvector.django import VectorField

class RagChunk(models.Model):
    ...
    embedding = VectorField(dimensions=384)

# Query becomes:
from pgvector.django import CosineDistance
RagChunk.objects.annotate(
    distance=CosineDistance('embedding', query_vec)
).order_by('distance')[:top_k]
```

Create index: `CREATE INDEX ON rag_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`

---

## Context Compression

### Trigger

After every AI plan response is saved, check:
```python
# core/services/ai_plan.py

def maybe_compress_context(plan_id: int):
    count = AIPlanDiscussion.objects.filter(plan_id=plan_id).count()
    if count >= settings.AI_PLAN_COMPRESSION_THRESHOLD:
        compress_plan_context(plan_id)
```

### Compression

```python
def compress_plan_context(plan_id: int):
    plan = AIPlan.objects.get(id=plan_id)
    messages = AIPlanDiscussion.objects.filter(
        plan_id=plan_id
    ).order_by('created_at')

    formatted = '\n\n'.join(
        f"[{m.role.upper()} – Step {m.step.step_number if m.step else 'plan-level'} "
        f"({m.created_at.strftime('%Y-%m-%d')})]\n{m.content}"
        for m in messages
    )

    summary = generate_once(
        system=(
            "You are summarizing a drug development planning conversation for a pharmaceutical AI system. "
            "Produce a structured summary covering: (1) project goal and constraints, "
            "(2) decisions made per step (step number, decision, rationale), "
            "(3) BioIntel entities created (type and ID), "
            "(4) experiment results that influenced the plan, "
            "(5) open questions or revision requests. "
            "Be concise but complete. This summary will replace the full history in future AI calls."
        ),
        user_content=formatted
    )

    plan.conversation_context = {
        'summary': summary,
        'compressed_at': timezone.now().isoformat(),
        'message_count': messages.count(),
    }
    plan.save()
```

### Injecting Context in Subsequent Calls

```python
def build_plan_messages(plan_id: int, step_id: int = None,
                        new_message: str = None) -> list[dict]:
    plan = AIPlan.objects.get(id=plan_id)
    messages = []

    # Prepend compressed summary if available
    if plan.conversation_context.get('summary'):
        messages.append({
            'role': 'user',
            'content': (
                f"[PLAN HISTORY SUMMARY — compressed from "
                f"{plan.conversation_context['message_count']} messages]\n\n"
                f"{plan.conversation_context['summary']}"
            )
        })
        messages.append({
            'role': 'assistant',
            'content': "Understood. I have the full project context."
        })

    # Add last N messages
    recent = AIPlanDiscussion.objects.filter(plan_id=plan_id)
    if step_id:
        recent = recent.filter(step_id=step_id)
    recent = list(recent.order_by('-created_at')[:settings.AI_PLAN_CONTEXT_WINDOW_MESSAGES])
    recent.reverse()
    for msg in recent:
        messages.append({'role': msg.role, 'content': msg.content})

    if new_message:
        messages.append({'role': 'user', 'content': new_message})

    return messages
```

---

## AI Plan State Machine

### States

| State | Description |
|---|---|
| `pending` | Not yet started; waiting for prior step to complete |
| `in_progress` | AI is generating recommendation (SSE stream active) |
| `awaiting_approval` | AI recommendation complete; waiting for scientist action |
| `approved` | Scientist approved; entities being created |
| `revision_needed` | Scientist requested changes; AI will re-generate |
| `completed` | Entities created; step fully done |
| `skipped` | Scientist skipped this step |
| `abandoned` | Step marked obsolete by a Go-Back-to-N action |

### Transitions

```
pending
  → in_progress       [trigger: previous step completed OR plan activated]

in_progress
  → awaiting_approval [trigger: AI finishes streaming]

awaiting_approval
  → approved          [trigger: scientist POSTs /approve/]
  → revision_needed   [trigger: scientist POSTs /reject/]

revision_needed
  → in_progress       [trigger: automatic after scientist submits discussion message]

approved
  → completed         [trigger: entity creation confirmed (synchronous in current impl)]

{awaiting_approval, in_progress, approved, completed}
  → abandoned         [trigger: Go-Back-to-N sets all steps from N onward to abandoned]

{any non-terminal state}
  → skipped           [trigger: scientist POSTs /skip/ — only allowed for non-required steps]
```

### Advance Plan Logic

```python
# core/services/ai_plan.py

def advance_plan(plan_id: int):
    """Called after a step transitions to 'completed'. Starts the next pending step."""
    plan = AIPlan.objects.get(id=plan_id)
    next_step = AIPlanStep.objects.filter(
        plan=plan, status='pending'
    ).order_by('step_number').first()

    if next_step:
        next_step.status = 'in_progress'
        next_step.save()
        plan.current_step_number = next_step.step_number
        plan.save()
        # Caller (view) will trigger stream_step_recommendation()
    else:
        plan.status = 'completed'
        plan.save()

def go_back_to_step(plan_id: int, target_step_number: int):
    """Abandons steps from target_step_number to current, creates fresh steps from target."""
    plan = AIPlan.objects.get(id=plan_id)
    current = plan.current_step_number

    # Abandon steps from target to current (inclusive)
    AIPlanStep.objects.filter(
        plan=plan,
        step_number__gte=target_step_number,
        step_number__lte=current,
    ).update(status='abandoned')

    # Create fresh pending steps from target onward
    # Re-use original step templates (titles, phases from the initial plan generation)
    # Fetch abandoned step data to re-create
    abandoned = AIPlanStep.objects.filter(
        plan=plan, status='abandoned',
        step_number__gte=target_step_number
    ).order_by('step_number')

    for old_step in abandoned:
        AIPlanStep.objects.create(
            plan=plan,
            step_number=old_step.step_number,
            phase=old_step.phase,
            title=old_step.title,
            description=old_step.description,
            status='pending' if old_step.step_number > target_step_number else 'in_progress',
        )

    plan.current_step_number = target_step_number
    plan.save()
```

---

## Extended `claude_client.py`

All new functions are added to the existing `core/services/claude_client.py`. The existing `stream_chat()`, `generate_once()`, and `build_project_context()` are unchanged.

### New Functions

```python
# core/services/claude_client.py (additions)

from core.services.rag import retrieve as rag_retrieve

PLAN_SYSTEM_PROMPT = """
You are a pharmaceutical AI expert assisting scientists in planning a drug development project on BioIntel.
You follow established methodology: ICH guidelines, Lipinski/Wager ADMET criteria, and peer-reviewed frameworks.
You NEVER make regulatory decisions — you recommend; scientists decide.
Every recommendation must cite at least one source from the pharmaceutical playbook:
  [Source: ICH Q6A Section 4.1] or [Source: Lipinski et al. 1997]
For small molecule projects, apply: Lipinski Rule of Five, Wager MPO, Gleeson ADMET thresholds.
For biologic projects, apply: ICH Q5-series, S6(R1), Jarasch developability criteria.
Use tools to fetch live data from external databases before making recommendations.
"""

PLAN_STEP_TOOLS = [
    # All 16 existing Chat Assistant tools (search_chembl, predict_admet, etc.) are included
    # Plus the following 4 new plan-write tools:
    {
        "name": "create_analog_candidate",
        "description": "Creates an analog candidate record in BioIntel for the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "smiles": {"type": "string"},
                "similarity_score": {"type": "number"},
                "patent_status": {"type": "string",
                                  "enum": ["free", "covered", "unknown"]},
                "notes": {"type": "string"},
            },
            "required": ["project_id", "smiles"],
        }
    },
    {
        "name": "create_synthesis_plan",
        "description": "Triggers ASKCOS retrosynthesis for a compound and saves the plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "compound_id": {"type": "integer"},
                "plan_type": {"type": "string", "enum": ["single_step", "multi_step"]},
            },
            "required": ["project_id", "compound_id", "plan_type"],
        }
    },
    {
        "name": "update_plan_step",
        "description": "Updates the recommendation and RAG sources for a plan step.",
        "input_schema": {
            "type": "object",
            "properties": {
                "step_id": {"type": "integer"},
                "recommendation": {"type": "object"},
                "entities_created": {"type": "array"},
                "rag_sources": {"type": "array"},
            },
            "required": ["step_id", "recommendation"],
        }
    },
    {
        "name": "mark_step_complete",
        "description": "Marks a plan step as completed with a final summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "step_id": {"type": "integer"},
                "summary": {"type": "string"},
            },
            "required": ["step_id", "summary"],
        }
    },
]


def stream_plan_generation(project_id: int, plan_id: int):
    """
    Generates the full AI-Driven Plan (all 15 steps) for a project.
    Streams SSE events: plan_step, text_delta, rag_citation, step_complete, plan_complete.
    Called when 'Generate AI-Driven Plan' is triggered.
    """
    plan = AIPlan.objects.get(id=plan_id)
    project_context = build_project_context(project_id)

    rag_context = rag_retrieve(
        query=f"drug development pipeline planning {plan.disease_description}",
        molecule_type=plan.molecule_type,
        project_id=project_id,
    )

    system = (
        f"{PLAN_SYSTEM_PROMPT}\n\n"
        f"PLAYBOOK REFERENCES:\n"
        + '\n'.join(f"[{c['document']}]: {c['text']}" for c in rag_context)
    )

    messages = [{'role': 'user', 'content': (
        f"Project context:\n{project_context}\n\n"
        f"Disease / condition: {plan.disease_description}\n"
        f"Molecule type: {plan.molecule_type}\n"
        f"Constraints: {plan.constraints}\n\n"
        "Generate a complete 15-step AI-Driven Plan for this project. "
        "For each step, provide: step_number, phase, title, description, "
        "and a brief recommendation with citations. "
        "Emit each step as a structured JSON object wrapped in <step>...</step> tags "
        "so the frontend can render the timeline progressively."
    )}]

    yield from _stream_with_tools(system, messages, PLAN_STEP_TOOLS)


def stream_step_recommendation(plan_id: int, step_id: int):
    """
    Generates the detailed recommendation for a single plan step.
    Called when a step transitions to in_progress.
    """
    step = AIPlanStep.objects.get(id=step_id)
    plan = AIPlan.objects.get(id=plan_id)
    project_context = build_project_context(plan.project_id)

    rag_context = rag_retrieve(
        query=f"{step.title} {step.description}",
        phase=step.phase,
        molecule_type=plan.molecule_type,
        project_id=plan.project_id,
    )

    system = (
        f"{PLAN_SYSTEM_PROMPT}\n\n"
        f"PLAYBOOK REFERENCES:\n"
        + '\n'.join(f"[{c['document']}]: {c['text']}" for c in rag_context)
    )

    messages = build_plan_messages(plan_id, step_id)
    if not messages:
        messages = [{'role': 'user', 'content': (
            f"Project context:\n{project_context}\n\n"
            f"Now working on Step {step.step_number}: {step.title}\n"
            f"Phase: {step.phase}\n"
            f"Description: {step.description}\n\n"
            "Provide a detailed recommendation for this step. "
            "Use your tools to fetch relevant data. "
            "Cite all ICH guidelines and papers you reference."
        )}]

    yield from _stream_with_tools(system, messages, PLAN_STEP_TOOLS)


def stream_step_discussion(plan_id: int, step_id: int, message: str):
    """
    Handles scientist messages in a step's discussion thread.
    """
    step = AIPlanStep.objects.get(id=step_id)
    plan = AIPlan.objects.get(id=plan_id)

    rag_context = rag_retrieve(
        query=message,
        phase=step.phase,
        molecule_type=plan.molecule_type,
        project_id=plan.project_id,
    )

    system = (
        f"{PLAN_SYSTEM_PROMPT}\n\n"
        f"You are discussing Step {step.step_number} ({step.title}) with the scientist.\n"
        f"Your current recommendation for this step:\n{step.ai_reasoning}\n\n"
        f"PLAYBOOK REFERENCES:\n"
        + '\n'.join(f"[{c['document']}]: {c['text']}" for c in rag_context)
    )

    messages = build_plan_messages(plan_id, step_id, new_message=message)
    yield from _stream_with_tools(system, messages, PLAN_STEP_TOOLS)


def stream_result_analysis(plan_id: int, step_id: int, experiment_results: dict):
    """
    Analyzes experiment results against the step's recommendation.
    Proposes: proceed / revise / go_back_to_step_N.
    """
    step = AIPlanStep.objects.get(id=step_id)
    plan = AIPlan.objects.get(id=plan_id)

    rag_context = rag_retrieve(
        query=f"experiment result analysis {step.title}",
        phase=step.phase,
        molecule_type=plan.molecule_type,
        project_id=plan.project_id,
    )

    system = (
        f"{PLAN_SYSTEM_PROMPT}\n\n"
        f"You are analyzing experiment results for Step {step.step_number}: {step.title}.\n"
        f"Original recommendation:\n{step.ai_reasoning}\n\n"
        f"PLAYBOOK REFERENCES:\n"
        + '\n'.join(f"[{c['document']}]: {c['text']}" for c in rag_context)
        + "\n\nEnd your response with a structured action block:\n"
          "<action>proceed</action> OR\n"
          "<action>revise</action> OR\n"
          "<action>go_back_to_step:<N></action>"
    )

    messages = [{
        'role': 'user',
        'content': (
            f"Experiment results for step {step.step_number}:\n"
            f"{json.dumps(experiment_results, indent=2)}\n\n"
            "Compare these results to the original plan recommendation. "
            "What is your assessment? What action do you recommend?"
        )
    }]

    yield from _stream_with_tools(system, messages, PLAN_STEP_TOOLS)


def stream_ai_panel_chat(project_id: int, page_type: str, page_entity: dict,
                         message: str, plan_step: dict = None,
                         plan_summary: str = None,
                         session_messages: list = None):
    """
    Powers the per-page AI panel.
    For AI-Driven projects: includes plan_step and plan_summary in context.
    For Manual projects: page_entity context only.
    """
    rag_context = rag_retrieve(
        query=message,
        project_id=project_id,
    )

    page_prompts = {
        'FormulationPlanningPage': (
            "You are a pharmaceutical formulation expert. "
            "Reference ICH Q8(R2), your knowledge of excipient chemistry, "
            "and FDA IIG limits when advising."
        ),
        'SynthesisPlanningPage': (
            "You are a synthetic chemistry expert. "
            "Reference ICH Q11 and retrosynthesis best practices."
        ),
        'StabilityPlanningPage': (
            "You are a stability science expert. "
            "Reference ICH Q1A(R2) at all times."
        ),
        'PreclinicalStudyPlannerPage': (
            "You are a preclinical development expert. "
            "Reference ICH M3(R2), S7A, S7B when advising on study design."
        ),
        # ... other page-specific prompts
    }

    page_prompt = page_prompts.get(page_type, "You are a drug development expert.")
    plan_context = ''
    if plan_step:
        plan_context = (
            f"\n\nCURRENT AI-DRIVEN PLAN STEP: Step {plan_step['step_number']} — "
            f"{plan_step['title']} ({plan_step['status']})\n"
            f"AI Recommendation: {plan_step.get('ai_reasoning', '')[:500]}..."
        )
    if plan_summary:
        plan_context += f"\n\nPLAN SUMMARY: {plan_summary}"

    system = (
        f"{page_prompt}\n\n"
        f"Current page: {page_type}\n"
        f"Page data: {json.dumps(page_entity, default=str)[:2000]}"
        f"{plan_context}\n\n"
        f"PLAYBOOK REFERENCES:\n"
        + '\n'.join(f"[{c['document']}]: {c['text']}" for c in rag_context)
    )

    messages = (session_messages or []) + [{'role': 'user', 'content': message}]
    yield from _stream_with_tools(system, messages, EXISTING_TOOLS)


def stream_ai_lab_intake(session_id: int, message: str, session_messages: list):
    """
    Powers the AI Lab intake chat.
    Conducts structured intake interview; produces project proposal when ready.
    """
    system = (
        "You are a drug development expert conducting an intake interview "
        "to help a scientist plan a new drug development project on BioIntel.\n\n"
        "Gather the following information conversationally (not as a form):\n"
        "1. Target disease/condition and patient population\n"
        "2. Development pathway: analog-based, novel small molecule, or biologic\n"
        "3. Molecule type (if biologic: modality preference)\n"
        "4. IP/mechanism constraints to avoid\n"
        "5. Starting stage: what existing data do they have?\n"
        "6. Timeline and risk appetite\n\n"
        "Ask 1-2 questions at a time. When you have enough information, "
        "output a structured project proposal wrapped in <proposal>...</proposal> tags "
        "containing: project_name, pathway, molecule_type, starting_phase, "
        "constraints (JSON), and a 3-step plan preview."
    )

    messages = session_messages + [{'role': 'user', 'content': message}]
    yield from _stream_with_tools(system, messages, EXISTING_TOOLS)
```

### Tool Handler Additions

```python
# core/views/ai_plan.py — _handle_plan_tool_call()

def _handle_plan_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == 'create_analog_candidate':
        from core.models import AnalogCandidate
        candidate = AnalogCandidate.objects.create(
            project_id=tool_input['project_id'],
            smiles=tool_input['smiles'],
            similarity_score=tool_input.get('similarity_score', 0),
            patent_status=tool_input.get('patent_status', 'unknown'),
            notes=tool_input.get('notes', ''),
            source='ai_driven',
        )
        return json.dumps({'created': True, 'id': candidate.id})

    elif tool_name == 'create_synthesis_plan':
        # Triggers ASKCOS and creates SynthesisPlan
        from core.services.askcos import run_retrosynthesis
        from core.models import Compound, SynthesisPlan
        compound = Compound.objects.get(id=tool_input['compound_id'])
        result = run_retrosynthesis(compound.smiles, tool_input['plan_type'])
        plan = SynthesisPlan.objects.create(
            project_id=tool_input['project_id'],
            compound=compound,
            plan_type=tool_input['plan_type'],
            result=result,
            source='ai_driven',
        )
        return json.dumps({'created': True, 'id': plan.id})

    elif tool_name == 'update_plan_step':
        step = AIPlanStep.objects.get(id=tool_input['step_id'])
        step.ai_recommendation = tool_input.get('recommendation', {})
        if tool_input.get('entities_created'):
            step.entities_created = tool_input['entities_created']
        if tool_input.get('rag_sources'):
            step.rag_sources = tool_input['rag_sources']
        step.save()
        return json.dumps({'updated': True})

    elif tool_name == 'mark_step_complete':
        step = AIPlanStep.objects.get(id=tool_input['step_id'])
        step.status = 'completed'
        step.ai_reasoning += f"\n\n[COMPLETION SUMMARY] {tool_input['summary']}"
        step.save()
        advance_plan(step.plan_id)
        return json.dumps({'completed': True})
```

---

## New Backend API Endpoints

All new endpoints are registered in `core/urls.py`.

### AI Plan Endpoints

```python
# AI Plan CRUD
path('projects/<int:pk>/ai-plan/',
     views.AIPlanView.as_view(), name='ai-plan'),
     # GET: returns plan + steps summary
     # POST: creates new AIPlan for project (status=draft)

path('ai-plans/<int:pk>/',
     views.AIPlanDetailView.as_view(), name='ai-plan-detail'),
     # GET: full plan with all steps
     # PATCH: update status, constraints

path('ai-plans/<int:pk>/generate/',
     views.AIPlanGenerateView.as_view(), name='ai-plan-generate'),
     # POST: SSE stream — triggers stream_plan_generation()

path('ai-plans/<int:pk>/compress-context/',
     views.AIPlanCompressView.as_view(), name='ai-plan-compress'),
     # POST: manually trigger context compression
```

### AI Plan Step Endpoints

```python
path('ai-plans/<int:plan_pk>/steps/',
     views.AIPlanStepListView.as_view(), name='ai-plan-steps'),
     # GET: all steps for a plan

path('ai-plan-steps/<int:pk>/',
     views.AIPlanStepDetailView.as_view(), name='ai-plan-step-detail'),
     # GET: step detail with full discussion
     # PATCH: update scientist_feedback, experiment_id

path('ai-plan-steps/<int:pk>/approve/',
     views.AIPlanStepApproveView.as_view(), name='ai-plan-step-approve'),
     # POST: transitions step to approved → completed; triggers next step

path('ai-plan-steps/<int:pk>/reject/',
     views.AIPlanStepRejectView.as_view(), name='ai-plan-step-reject'),
     # POST: body: {feedback: "..."} → sets revision_needed + saves feedback

path('ai-plan-steps/<int:pk>/skip/',
     views.AIPlanStepSkipView.as_view(), name='ai-plan-step-skip'),
     # POST: sets step to skipped; triggers next pending step

path('ai-plan-steps/<int:pk>/discuss/',
     views.AIPlanStepDiscussView.as_view(), name='ai-plan-step-discuss'),
     # POST: body: {message: "..."} → SSE: stream_step_discussion()
     # Saves scientist message + AI response to AIPlanDiscussion

path('ai-plan-steps/<int:pk>/recommend/',
     views.AIPlanStepRecommendView.as_view(), name='ai-plan-step-recommend'),
     # POST: SSE: stream_step_recommendation() for in_progress steps

path('ai-plan-steps/<int:pk>/analyze-results/',
     views.AIPlanStepAnalyzeView.as_view(), name='ai-plan-step-analyze'),
     # POST: body: {experiment_id: N} → SSE: stream_result_analysis()

path('ai-plan-steps/<int:pk>/go-back/',
     views.AIPlanGoBackView.as_view(), name='ai-plan-go-back'),
     # POST: body: {target_step_number: N} → calls go_back_to_step()
```

### AI Lab Endpoints

```python
path('ai-lab/sessions/',
     views.AILabSessionListView.as_view(), name='ai-lab-sessions'),
     # GET: list all intake sessions
     # POST: create new session

path('ai-lab/sessions/<int:pk>/messages/',
     views.AILabSessionMessageView.as_view(), name='ai-lab-messages'),
     # POST: body: {content: "..."} → SSE: stream_ai_lab_intake()

path('ai-lab/sessions/<int:pk>/create-project/',
     views.AILabCreateProjectView.as_view(), name='ai-lab-create-project'),
     # POST: body: {confirmed_proposal: {...}}
     # Creates Project + AIPlan + AIPlanSteps atomically
     # Returns {project_id, plan_id, redirect_url}
```

### Per-Page AI Panel Endpoint

```python
path('projects/<int:pk>/ai-panel/chat/',
     views.AIPagePanelChatView.as_view(), name='ai-panel-chat'),
     # POST: body: {page_type, page_entity_id, message, session_messages}
     # GET plan context if project.mode == 'ai_driven'
     # SSE: stream_ai_panel_chat()
```

### Document Portal Endpoints

```python
path('documents/',
     views.RagDocumentListView.as_view(), name='documents'),
     # GET: list all documents (with filters: type, molecule_type, phase, project)
     # POST: upload new document (multipart/form-data)

path('documents/<int:pk>/',
     views.RagDocumentDetailView.as_view(), name='document-detail'),
     # GET: document detail with chunk count
     # PATCH: update metadata (name, type, phase_relevance, project)
     # DELETE: deletes document + all chunks

path('documents/<int:pk>/ingest/',
     views.DocumentIngestView.as_view(), name='document-ingest'),
     # POST: (re)triggers ingestion pipeline

path('documents/search/',
     views.DocumentSearchView.as_view(), name='document-search'),
     # GET: ?q=<query>&project=<id>&type=<type>
     # Returns top matching chunks with document context
```

### Biologics Endpoints

```python
# Cell Line Development
path('projects/<int:pk>/cell-line/',
     views.CellLineView.as_view()),

# Bioprocess Development
path('projects/<int:pk>/bioprocessing/',
     views.BioprocessView.as_view()),

# Downstream Purification
path('projects/<int:pk>/purification/',
     views.DownstreamPurificationView.as_view()),

# Biologics Formulation
path('projects/<int:pk>/biologic-formulation/',
     views.BiologicsFormulationView.as_view()),

# Biologics Characterization Methods
path('projects/<int:pk>/biologic-analytics/',
     views.BiologicsAnalyticsListView.as_view()),
path('biologic-analytics/<int:pk>/',
     views.BiologicsAnalyticsDetailView.as_view()),
```

---

## New Frontend Components

### New Pinia Stores

**`frontend/src/stores/aiPlan.js`**
```javascript
export const useAIPlanStore = defineStore('aiPlan', {
  state: () => ({
    plan: null,
    steps: [],
    activeStepId: null,
    discussions: {},       // { step_id: [messages] }
    streaming: false,
    streamingStepId: null,
    streamingText: '',
    planGenerating: false,
  }),
  actions: {
    async fetchPlan(projectId) { ... },
    async generatePlan(planId) { ... },        // opens SSE
    async approveStep(stepId) { ... },
    async rejectStep(stepId, feedback) { ... },
    async discussStep(stepId, message) { ... }, // opens SSE
    async analyzeResults(stepId, experimentId) { ... },
    async goBack(stepId, targetStepNumber) { ... },
    handleSSEEvent(event) {
      // plan_step: add step to timeline
      // text_delta: append to streamingText
      // step_complete: update step status, stop streaming
      // plan_complete: set planGenerating=false
    }
  }
})
```

**`frontend/src/stores/aiLab.js`**
```javascript
export const useAILabStore = defineStore('aiLab', {
  state: () => ({
    sessions: [],
    activeSession: null,
    messages: [],
    streaming: false,
    streamingText: '',
    pendingProposal: null,   // parsed <proposal>...</proposal> from stream
  }),
  actions: {
    async fetchSessions() { ... },
    async createSession() { ... },
    async sendMessage(sessionId, content) { ... },  // opens SSE
    async createProject(sessionId, proposal) { ... },
  }
})
```

**`frontend/src/stores/documents.js`**
```javascript
export const useDocumentsStore = defineStore('documents', {
  state: () => ({
    documents: [],
    uploading: false,
    uploadProgress: 0,
    searchResults: [],
  }),
  actions: {
    async fetchDocuments(filters) { ... },
    async uploadDocument(file, metadata) { ... },
    async deleteDocument(id) { ... },
    async reingestDocument(id) { ... },
    async search(query, projectId) { ... },
  }
})
```

### New Page Components

**`frontend/src/views/AILabPage.vue`**
- Two-column layout: session list (260px) + main chat panel
- `AILabSessionList` component: session cards with title, date, status
- Main panel: `AILabChatPanel` with streaming markdown + proposal card
- Proposal card: rendered when `<proposal>...</proposal>` detected in stream
- "Create Project & Plan" button: calls `aiLabStore.createProject()`, redirects to project

**`frontend/src/views/DocumentPortalPage.vue`**
- Upload zone: `DocumentUploader` component with drag-drop, progress bar, metadata form
- Document list: card grid with `DocumentCard` component
- Search: `SearchInput` debounced → `documentsStore.search()`
- Filters: document type, molecule type, phase relevance, project

**`frontend/src/views/CellLineDevelopmentPage.vue`**
- Four tabs: Expression System | Transfection Strategy | Clone Selection | Cell Bank Plan
- Preset chips for expression systems
- Status selector per phase
- AI panel surfaces Step 6 recommendation (biologic plan)

**`frontend/src/views/UpstreamBioprocessingPage.vue`**
- Scale tabs: Microscale | Bench | Pilot | Manufacturing
- CPP parameter table with target + range fields per parameter
- CQA tracking table
- Media + feed strategy textareas
- ICH Q8(R2) reference card for CPP/CQA definitions

**`frontend/src/views/DownstreamPurificationPage.vue`**
- Purification train builder: drag-to-reorder steps (unit operation cards)
- Per-step: entry criteria, conditions, pool criteria, expected yield
- Running mass balance displayed at bottom
- Impurity clearance target table (HCP, DNA, endotoxin, monomer)

**`frontend/src/views/BiologicsAnalyticsPage.vue`**
- Left panel: method list grouped by method type
- Right panel: per-method detail (same 4-tab structure as v2 AnalyticalMethodPage)
- Method-type-specific parameter forms (SEC-HPLC, icIEF, glycan, etc.)
- ICH Q6B reference panel

**`frontend/src/views/BiologicsFormulationPage.vue`**
- Five tabs: Target | Buffer Screening | Stabilizer Screening | Container Closure | Lyophilization
- Buffer matrix builder: 3 buffers × 3 pH values
- Stress conditions tracking (thermal, mechanical, freeze-thaw)
- Lyo cycle designer with Tg′ field

### New Reusable Components

**`frontend/src/components/ai/AIPlanTimeline.vue`**
```
Props: { planId, projectId }
Renders: vertical list of AIPlanStepCard components
State: reads from aiPlanStore
Scroll behavior: active step auto-scrolled into view
Empty state: "Generate AI-Driven Plan" card
```

**`frontend/src/components/ai/AIPlanStepCard.vue`**
```
Props: { step }
Renders:
  - Status circle (left gutter, colored by status)
  - Phase badge
  - Step number + title
  - Status badge (colored)
  - AI recommendation preview (first 2 lines, shown when status != pending)
  - RAG citation pills
  - Action buttons (context-sensitive per status)
  - Inline discussion panel (expanded when discussOpen = true)
Emits: approve, reject, discuss, skip, goBack
```

**`frontend/src/components/ai/AIPlanDiscussionPanel.vue`**
```
Props: { planId, stepId }
Renders:
  - Full AI reasoning (expandable)
  - RAG citations (expandable block per citation, shows full chunk text)
  - Discussion thread (scientist + AI messages)
  - StreamingIndicator when streaming
  - Message input + send button
Behavior:
  - Fetches discussions from aiPlanStore.discussions[stepId]
  - On send: calls aiPlanStore.discussStep(stepId, message)
  - Handles streaming events: text_delta, tool_use, message_stop
```

**`frontend/src/components/ai/AIPagePanel.vue`**
```
Props: { projectId, pageType, pageEntityId }
Renders:
  - Collapsible panel (300px, right side)
  - Header: page-type label + collapse toggle
  - If AI-Driven + current step matches page: step recommendation card at top
  - Chat thread with MarkdownRenderer + StreamingIndicator
  - Tool call badges inline
  - Sources expandable
  - Input: text + send + file attach button
State:
  - sessionMessages: local ref (session-only for Manual; saved to plan discussions for AI-Driven)
  - streaming: ref
  - streamingText: ref
Actions:
  - sendMessage() → POST /api/projects/<id>/ai-panel/chat/ → SSE stream
  - attachFile() → upload to Document Portal, then reference in message
```

**`frontend/src/components/ai/PlanStepStatusBadge.vue`**
```
Props: { status }
Renders: pill badge with color-coded background
Colors:
  pending: grey (#6b7280)
  in_progress: blue (#2563eb) with pulsing animation
  awaiting_approval: amber (#d97706)
  approved: green (#059669)
  revision_needed: orange (#ea580c)
  completed: green (#059669) + checkmark
  skipped: grey (#9ca3af) + strikethrough text
  abandoned: grey (#9ca3af) + strikethrough text
```

**`frontend/src/components/documents/DocumentUploader.vue`**
```
Props: { projectId (optional) }
Renders:
  - Drag-drop zone with dashed border + upload icon
  - File type + size restrictions shown
  - On file drop/select: shows metadata form inline
  - Progress bar during upload
  - Success: shows document card preview with ingestion status
Emits: uploaded(documentId)
```

### Modified Existing Components

**`frontend/src/views/ProjectPage.vue`** — additions:
- Import `AIPlanTimeline` component
- Add computed `isAIDriven = project.mode === 'ai_driven'`
- Render `<AIPlanTimeline :plan-id="plan?.id" :project-id="projectId" />` in new "AI-Driven Plan" section
- Add "Generate AI-Driven Plan" card when `isAIDriven && !plan`
- "Upgrade to AI-Driven" button in project settings area when `project.mode === 'manual'`

**`frontend/src/views/ProjectSetupPage.vue`** — additions:
- "Project Mode" toggle: Manual / AI-Driven (styled radio buttons with descriptions)
- When AI-Driven selected: molecule type selector appears (Small Molecule / Biologic / Not yet determined)
- For AI-Driven projects: note "After creation, you can generate the AI-Driven Plan from the project page or visit AI Lab first"

**`frontend/src/components/layout/SideNav.vue`** — additions:
- "AI Lab" item at top of nav (below logo, above Dashboard)
- "Documents" item below Research section
- Biologics sub-items added to per-project nav, conditionally shown when `project.molecule_type === 'biologic'`:
  - Drug Substance: "Cell Line Development", "Upstream Bioprocessing" (replace Synthesis Hub, Salt & Polymorph)
  - Drug Product: "Downstream Purification", "Biologics Formulation" (replace Formulation Planning, Stability)
  - Analytical: adds "Biologics Analytics" below Methods
- Chat Assistant item: hidden for AI-Driven projects (per-page panel replaces it)

**`frontend/src/App.vue`** — additions:
```javascript
// Mount AIPagePanel conditionally
const showAIPanel = computed(() => {
  const projectPages = [
    'ProjectPage', 'SARTracker', 'CandidateSelection',
    'SynthesisHub', 'SaltPolymorphScreening', 'ProcessDevelopment',
    'FormulationPlanning', 'StabilityPlanning', 'AnalyticalMethod',
    'SpecificationBuilder', 'ADMETDashboard', 'PreclinicalStudyPlanner',
    'RiskAssessment', 'CompoundProfile',
    // biologics pages
    'CellLineDevelopment', 'UpstreamBioprocessing', 'DownstreamPurification',
    'BiologicsAnalytics', 'BiologicsFormulation',
  ]
  return projectPages.includes(route.name) && route.params.id
})
```
```html
<div class="app-layout" :class="{ 'with-panel': showAIPanel }">
  <SideNav />
  <div class="main-content">
    <TopBar />
    <router-view />
  </div>
  <AIPagePanel v-if="showAIPanel"
               :project-id="route.params.id"
               :page-type="route.name"
               :page-entity-id="pageEntityId" />
</div>
```

---

## SSE Streaming Patterns

### Existing Pattern (v2)

All streaming uses Django `StreamingHttpResponse` with `Content-Type: text/event-stream`. The frontend consumes via `createSSEStream()` async generator in `api.js`.

### New SSE Event Types (v3)

The `createSSEStream()` function already handles arbitrary event types. New event types added:

```javascript
// frontend/src/services/api.js — extend createSSEStream handler

// Existing (v2)
{ type: 'text_delta', text: '...' }
{ type: 'tool_use', name: '...', input: {...} }
{ type: 'tool_result', name: '...', result: {...} }
{ type: 'sources', sources: [...] }
{ type: 'message_stop' }

// New (v3)
{ type: 'plan_step', step_number: 3, phase: 'discovery',
  title: 'Patent Landscape Review', description: '...' }
  // → aiPlanStore adds/updates step in timeline

{ type: 'step_complete', step_id: 42, status: 'awaiting_approval' }
  // → aiPlanStore updates step status; streaming stops for that step

{ type: 'plan_complete', step_count: 15 }
  // → aiPlanStore sets planGenerating=false

{ type: 'rag_citation', document: 'ICH Q6A', chunk_index: 3,
  text_preview: 'Section 4.1 states...' }
  // → appended to sources list in current message

{ type: 'result_action', action: 'proceed' | 'revise' | 'go_back',
  target_step: null | N }
  // → post-experiment analysis: drives UI decision buttons

{ type: 'proposal', project_name: '...', pathway: '...',
  molecule_type: '...', starting_phase: '...',
  constraints: {...}, preview_steps: [...] }
  // → AI Lab: renders proposal card in intake chat
```

### Backend SSE Response Pattern (same as v2, extended)

```python
# core/views/ai_plan.py

class AIPlanGenerateView(APIView):
    def post(self, request, pk):
        plan = get_object_or_404(AIPlan, project_id=pk)

        def event_stream():
            for event in stream_plan_generation(pk, plan.id):
                yield f"data: {json.dumps(event)}\n\n"
                # Save AI responses to AIPlanDiscussion as they complete
                if event['type'] == 'message_stop':
                    save_ai_response(plan, full_text, tool_calls, sources)
                    maybe_compress_context(plan.id)

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
```

---

## New Frontend Routes

```javascript
// frontend/src/router/index.js — additions

{ path: '/ai-lab',
  name: 'AILab',
  component: () => import('@/views/AILabPage.vue') },

{ path: '/documents',
  name: 'DocumentPortal',
  component: () => import('@/views/DocumentPortalPage.vue') },

{ path: '/projects/:id/ai-plan',
  name: 'AIPlan',
  component: () => import('@/views/AIPlanDetailPage.vue') },

// Biologics
{ path: '/projects/:id/cell-line',
  name: 'CellLineDevelopment',
  component: () => import('@/views/CellLineDevelopmentPage.vue') },

{ path: '/projects/:id/bioprocessing',
  name: 'UpstreamBioprocessing',
  component: () => import('@/views/UpstreamBioprocessingPage.vue') },

{ path: '/projects/:id/purification',
  name: 'DownstreamPurification',
  component: () => import('@/views/DownstreamPurificationPage.vue') },

{ path: '/projects/:id/biologic-analytics',
  name: 'BiologicsAnalytics',
  component: () => import('@/views/BiologicsAnalyticsPage.vue') },

{ path: '/projects/:id/biologic-formulation',
  name: 'BiologicsFormulation',
  component: () => import('@/views/BiologicsFormulationPage.vue') },
```

---

## Biologics Technical Notes

### Small Molecule Features Disabled for Biologic Projects

The following v2 features are disabled when `project.molecule_type === 'biologic'`:

| Feature | Reason |
|---|---|
| Virtual Screening (ASKCOS docking) | No small molecule synthesis for protein-based therapeutics |
| Synthesis Planning (ASKCOS retrosynthesis) | Proteins are expressed, not synthesized chemically |
| Salt & Polymorph Screening | Not applicable to biologics (buffer/pH screening replaces this) |
| pkCSM ADMET predictions | pkCSM is trained on small molecules; invalid for biologics |
| Lipinski/Wager/Gleeson filters | Rule of Five does not apply to proteins |

Frontend: these nav items are hidden and their pages redirect to a "Not available for biologic projects" notice when `molecule_type === 'biologic'`.

### Biologic-Specific External APIs

New service modules in `core/services/`:

| Module | File | Purpose |
|---|---|---|
| IMGT/V-QUEST | `imgt.py` | Antibody germline assignment, CDR identification |
| UniProt sequence | `uniprot.py` (extended) | Full sequence retrieval, isoforms |
| FDA Purple Book | `purplebook.py` | Licensed biologic products reference |

```python
# IMGT V-QUEST is web-based; for dev, use local germline database fallback
# or the BioPython antibody analysis tools

# core/services/imgt.py
def analyze_vhvl_sequences(vh_seq: str, vl_seq: str) -> dict:
    """
    Returns: germline_vh, germline_vl, cdr_regions,
             humanization_pct, immunogenicity_flags
    """
```

### Biologic Compound Record

The `Compound` model's new `sequence` field stores:
- For antibodies: VH sequence (FASTA format, one-letter amino acid code)
- For Fc-fusions, peptides: full protein sequence
- `smiles` field: null for biologics (no chemical structure)
- `molecular_weight`: calculated from sequence if SMILES is null

Frontend: `CompoundProfilePage` detects `compound.sequence` and renders sequence viewer instead of 2D structure when sequence is present.

---

## AI-Driven Plan System Prompt Reference

### Small Molecule System Prompt

The full system prompt injected for all small molecule AI-Driven Plan calls:

```
You are a pharmaceutical development expert and BioIntel AI assistant.
Your role is to guide drug development teams through the complete small molecule
drug development pipeline, from target identification through IND-enabling studies.

METHODOLOGY:
You follow established frameworks:
- Drug discovery: Bleicher et al. 2003 (hit-to-lead), Hopkins & Groom 2002 (target selection)
- Lead optimization: Lipinski Rule of Five (MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10),
  Wager MPO score, Gleeson ADMET thresholds
- Candidate progression: hERG IC50 > 10 μM (go threshold), AMES negative,
  Caco-2 Papp ≥ 1×10⁻⁶ cm/s, F > 20%, t½ > 2h
- Development: ICH Q6A (specifications), Q8(R2) (pharmaceutical development),
  Q11 (drug substance), Q1A(R2) (stability), Q2(R1) (analytical validation)
- Preclinical: ICH M3(R2) (study design), S7A/S7B (safety pharmacology),
  S2(R1) (genotoxicity)

CITATION REQUIREMENT:
Every recommendation must cite at least one source:
  [Source: ICH Q6A, Section 4.1.1]
  [Source: Lipinski et al. 1997, Rule of Five criteria]
  [Source: Gleeson 2008, Table 1 ADMET thresholds]

BOUNDARIES:
- You recommend; scientists decide. Never say "this must be done" — say "this is recommended based on [source]"
- You do not predict clinical outcomes
- You do not provide legal advice on patent freedom-to-operate (flag risks, but defer to IP counsel)
- When data is insufficient, say so explicitly rather than speculating
```

### Biologic System Prompt

```
You are a pharmaceutical biologics development expert and BioIntel AI assistant.
Your role is to guide development teams through the complete biologic drug development
pipeline, from antigen identification through BLA-enabling studies.

METHODOLOGY:
- Antibody design: Carter 2006, Jain et al. 2017 biophysical benchmarks
- Developability: Jarasch et al. 2015 (aggregation, pI, viscosity, chemical liabilities)
- Cell line development: ICH Q5B (expression construct analysis)
- Viral safety: ICH Q5A(R2)
- Stability: ICH Q5C
- Comparability: ICH Q5E
- Specifications: ICH Q6B
- Preclinical safety: ICH S6(R1) (species selection, immunogenicity monitoring)

CITATION REQUIREMENT: same as small molecule.

BOUNDARIES: same as small molecule.
```

---

## Management Commands

### `python manage.py ingest_rag_corpus`

Ingests all PDFs in `RAG_CORPUS_DIR` into the global playbook corpus.

```
Options:
  --corpus-dir PATH   Directory containing documents (default: settings.RAG_CORPUS_DIR)
  --document-type     ich_guideline | academic_paper | ... (default: ich_guideline)
  --force-reingest    Re-ingest documents that are already 'ready'
```

### `python manage.py seed_playbook`

Seeds the playbook metadata records (no PDFs needed) so the system knows which documents are expected. Used to initialize the `rag_documents` table with the canonical playbook list before PDFs are placed in the corpus directory.

```
Creates RagDocument records (ingestion_status=pending) for:
  - All ICH guidelines listed in the playbook
  - All academic papers listed in the playbook
Run ingest_rag_corpus afterward to actually ingest them.
```

### `python manage.py check_rag_corpus`

Validates that all expected playbook documents are ingested and ready.

```
Output:
  ✓ ICH Q1A(R2) — 1,234 chunks
  ✓ ICH Q2(R1) — 892 chunks
  ✗ Lipinski 1997 — NOT INGESTED (place PDF in /rag_corpus/small_molecule/discovery/)
  ...
  Summary: 18/24 documents ready
```

---

## CSS Additions

New CSS custom properties for v3 UI elements:

```css
/* frontend/src/style.css — additions */

/* AI Plan step status colors */
--step-pending: #6b7280;
--step-in-progress: #2563eb;
--step-awaiting: #d97706;
--step-approved: #059669;
--step-revision: #ea580c;
--step-completed: #059669;
--step-skipped: #9ca3af;
--step-abandoned: #9ca3af;

/* AI Panel */
--panel-width: 300px;
--panel-bg: #f8fafc;
--panel-border: #e2e8f0;
--panel-header-bg: #1e40af;
--panel-header-text: #ffffff;

/* RAG citation badges */
--rag-badge-bg: #eff6ff;
--rag-badge-text: #1d4ed8;
--rag-badge-border: #bfdbfe;

/* Biologics indicators */
--biologic-accent: #7c3aed;
--biologic-light: #f5f3ff;

/* Layout with panel */
.app-layout.with-panel {
  display: grid;
  grid-template-columns: 240px 1fr var(--panel-width);
}

/* Pulsing animation for in_progress step */
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(37, 99, 235, 0); }
  100% { box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }
}
.step-circle.in-progress {
  animation: pulse-ring 2s ease-out infinite;
}
```

---

## Migration Summary

| Migration | Contents |
|---|---|
| `0013_v3_project_fields` | Adds `mode`, `molecule_type` to `Project`; adds `sequence` to `Compound` |
| `0014_ai_plan_tables` | Creates `AIPlan`, `AIPlanStep`, `AIPlanDiscussion` |
| `0015_rag_tables` | Creates `RagDocument`, `RagChunk` |
| `0016_biologics_tables` | Creates `CellLineDevelopment`, `BioprocessDevelopment`, `DownstreamPurification`, `BiologicsFormulation`, `BiologicsCharacterizationMethod` |

All existing v2 data is safe. Default values:
- All existing `Project` records: `mode='manual'`, `molecule_type='small_molecule'`
- All existing `Compound` records: `sequence=null`

No data migration scripts required — Django `AddField` with `default` handles all existing rows.

---

## v3 Page Inventory

### New Pages (v3)

| Page Component | Route | Module |
|---|---|---|
| `AILabPage` | `/ai-lab` | Module 11 |
| `DocumentPortalPage` | `/documents` | Module 14 |
| `AIPlanDetailPage` | `/projects/:id/ai-plan` | Module 12 |
| `CellLineDevelopmentPage` | `/projects/:id/cell-line` | Module 15C |
| `UpstreamBioprocessingPage` | `/projects/:id/bioprocessing` | Module 15D |
| `DownstreamPurificationPage` | `/projects/:id/purification` | Module 15E |
| `BiologicsAnalyticsPage` | `/projects/:id/biologic-analytics` | Module 15F |
| `BiologicsFormulationPage` | `/projects/:id/biologic-formulation` | Module 15G |

### Modified Pages (v3)

| Page Component | Changes |
|---|---|
| `ProjectPage` | + AI-Driven Plan section, + "Upgrade to AI-Driven" action |
| `ProjectSetupPage` | + mode toggle, + molecule_type selector |
| `CompoundProfilePage` | + sequence viewer for biologic compounds |
| All 22 v2 project pages | + AI panel integration (per-page context injected) |

### Total Page Count: 30 (v2) + 8 (new) = 38 pages

---

## Implementation Update — v3.1 (Manual AI Panel)

> **Date:** 2026-06-02  
> **Scope:** Per-page AI panel fully wired for Manual projects — ask-then-confirm suggestions, per-page persistent chat history, RAG retrieve bug fix.

### New Files

| File | Purpose |
|---|---|
| `frontend/src/stores/aiPanelContext.js` | Pinia store — per-page chat histories keyed by `${projectId}_${pageType}`, apply trigger, entity data |
| `frontend/src/services/aiPageContexts.js` | `PAGE_FIELD_SCHEMAS` map (11 page types → field definitions); `getFieldLabel()` helper |
| `frontend/src/composables/useAIPageContext.js` | Composable that wires a page's entity data into the store and watches `applyTrigger` to call the page's apply function |
| `frontend/src/components/ai-plan/SuggestionCard.vue` | Renders the checkboxed field suggestion list with Apply All / Apply Selected |

### `aiPanelContext` Store — Key Contracts

```javascript
// State
chatHistories: {},      // key: `${projectId}_${pageType}` → Message[]
currentPageType: null,
currentProjectId: null,
currentEntityData: {},  // current page's form data; sent as page_entity to backend
pendingSuggestions: null,
applyTrigger: 0,        // incremented on each Apply — watched by useAIPageContext

// Getters
pageKey          // `${currentProjectId}_${currentPageType}` or null
currentMessages  // chatHistories[pageKey] or []

// Actions
setPageContext(pageType, projectId, entityData)  // called on page mount / watchEffect
addMessage(role, content, suggestion = null)     // appends to chatHistories[pageKey]
triggerApply(selectedFields)  // sets pendingSuggestions + increments applyTrigger
clearHistory(pageType, projectId)               // deletes chatHistories key
```

**Chat history persistence:** histories live in the Pinia store for the browser session. They are not serialized to localStorage — refreshing the page clears them. This is intentional for Manual mode; AI-Driven plan discussions are persisted server-side via `AIPlanDiscussion`.

### `useAIPageContext` Composable

```javascript
// frontend/src/composables/useAIPageContext.js
export function useAIPageContext({ pageType, projectIdRef, getEntity, applyFn }) {
  const store = useAIPanelContextStore()

  // Sync page entity into store whenever it changes
  watchEffect(() => {
    const id = typeof projectIdRef === 'function' ? projectIdRef() : projectIdRef?.value
    if (id) store.setPageContext(pageType, id, getEntity ? getEntity() : {})
  })

  // Apply AI suggestions to page form when Apply is clicked in the panel
  watch(() => store.applyTrigger, () => {
    if (store.pendingSuggestions && applyFn) applyFn(store.pendingSuggestions)
  })
}
```

**Usage in a page component:**
```javascript
useAIPageContext({
  pageType: 'FormulationPlanningPage',
  projectIdRef: computed(() => parseInt(route.params.id)),
  getEntity: () => ({ ...newPlanForm.value }),
  applyFn: (suggestions) => {
    Object.entries(suggestions).forEach(([k, v]) => {
      if (k in newPlanForm.value) newPlanForm.value[k] = v
    })
  },
})
```

### Suggestion Flow — End-to-End

```
1. User asks question in AIPagePanel
2. AIPagePanel sends POST /api/projects/<id>/ai-panel/chat/ with:
     { message, page_type, page_entity: store.currentEntityData, session_messages }
3. Backend stream_ai_panel_chat():
     - Builds page_block from PAGE_CONTEXTS[page_type]: field list + current values
     - Appends _SUGGESTION_INSTRUCTION to system prompt
     - Streams response via SSE
4. AI appends <suggestion>{"key": "value"}</suggestion> at end of response
5. AIPagePanel.parseSuggestion(fullText):
     - Extracts JSON from <suggestion>...</suggestion>
     - Returns { displayText, suggestion }
6. store.addMessage('assistant', displayText, suggestion)
7. SuggestionCard rendered below the assistant message
8. User clicks Apply → store.triggerApply(selectedFields)
9. useAIPageContext watcher fires → applyFn(selectedFields) → form fields update
```

### Backend Changes — `claude_client.py`

**`PAGE_CONTEXTS` dict** (11 entries, one per page type):
```python
PAGE_CONTEXTS = {
    'FormulationPlanningPage': {
        'label': 'Formulation Planning',
        'guidance': 'You are a pharmaceutical formulation expert... Reference ICH Q8(R2)...',
        'fields': [
            ('dosage_form', 'Dosage Form', 'e.g. tablet, capsule, injection'),
            ('route_of_administration', 'Route of Administration', 'e.g. oral, IV, SC'),
            ...
        ],
    },
    ...  # StabilityPlanningPage, SARTrackerPage, SpecificationBuilderPage,
         # PreclinicalStudyPlannerPage, AnalyticalMethodPage, SaltPolymorphScreeningPage,
         # ProcessDevelopmentPage, SynthesisHubPage, ADMETDashboardPage, ProjectSetupPage
}
```

**`_SUGGESTION_INSTRUCTION`** injected at end of every panel system prompt:
```python
_SUGGESTION_INSTRUCTION = """
## Suggestion Format
When you have concrete, evidence-based values to recommend for the form fields listed above,
append the following block at the VERY END of your response:
<suggestion>{"field_key": "value"}</suggestion>
Rules: use exact field keys; strings only; valid JSON; omit block if no concrete suggestions.
"""
```

**`stream_ai_panel_chat()` system prompt construction:**
```python
ctx = PAGE_CONTEXTS.get(page_type)
if ctx:
    fields_text = '\n'.join(
        f"  - {key} ({label}){': ' + hint if hint else ''}: currently = {page_entity.get(key, '(empty)')}"
        for key, label, *rest in ctx['fields']
        for hint in ([rest[0]] if rest else [''])
    )
    page_block = f"## Page: {ctx['label']}\n{ctx['guidance']}\n\nForm fields:\n{fields_text}"
else:
    page_block = f"## Page: {page_type}\nYou are a drug development expert."

system = page_block + '\n\n' + _SUGGESTION_INSTRUCTION + '\n\nPlaybook references:\n' + rag_block
```

### RAG Retrieve Bug Fix

**Problem:** `rag.py retrieve()` crashed with `TypeError: cannot unpack non-iterable NoneType object` when the AI panel was first used. A `models_Q := None` walrus operator placeholder from an earlier draft had been left as the argument to `.filter()`, which Django passed through as `None`, causing the ORM to try to unpack it.

**Fix:** Removed the 4-line broken block entirely. The correct project-scope filtering using `django.db.models.Q` was already present below it:
```python
# Before (broken):
doc_qs.filter(models_Q := None  # handled below via Python)

# After (correct — was already present lower in the function):
from django.db.models import Q
qs = qs.filter(Q(document__project__isnull=True) | Q(document__project_id=project_id))
```

### TopBar AI Assistant Toggle

**Problem:** The AI Assistant toggle button was placed in an unstyled div below the TopBar, making it invisible.

**Fix:** Added `<slot name="actions" />` to `TopBar.vue` (before the product name span). `App.vue` injects the toggle button into this slot conditionally when on a project page:
```html
<TopBar>
  <template v-if="showPanelToggle" #actions>
    <button class="panel-toggle-btn" @click="panelOpen = !panelOpen">✦ AI Assistant</button>
  </template>
</TopBar>
```

### Build Output

Clean build at **188 modules** (up from 183 in v3.0). New modules include:
- `useAIPageContext-*.js`
- `SuggestionCard` (bundled into `index-*.js`)
- `aiPanelContext` store (bundled into `index-*.js`)
- `aiPageContexts` service (bundled into `index-*.js`)

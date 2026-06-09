"""
RAG pipeline: embedding, retrieval, and document ingestion helpers.

Dev: embeddings stored as JSON in SQLite; cosine sim via numpy.
Prod: migrate to pgvector + `<=>` operator.
"""

import logging
import math
import os
import re

import numpy as np

logger = logging.getLogger(__name__)

_embedding_model = None

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
TOP_K_DEFAULT = 5


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def embed(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def _cosine_sim(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    dot = float(np.dot(va, vb))
    norm_a = float(np.linalg.norm(va))
    norm_b = float(np.linalg.norm(vb))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve(
    query: str,
    phase: str | None = None,
    molecule_type: str | None = None,
    project_id: int | None = None,
    top_k: int = TOP_K_DEFAULT,
) -> list[dict]:
    """Return top_k RAG chunks most relevant to query.

    Filters:
    - molecule_type: skip chunks from docs that don't match (small_molecule / biologic / both)
    - phase: skip chunks from docs whose phase_relevance list doesn't include the phase
    - project_id: include global docs (project=None) + project-scoped docs
    """
    from core.models import RagChunk, RagDocument

    # Build candidate chunk queryset
    doc_qs = RagDocument.objects.filter(ingestion_status='ready')
    if molecule_type and molecule_type != 'undetermined':
        doc_qs = doc_qs.filter(molecule_type__in=[molecule_type, 'both'])
    ready_doc_ids = set(doc_qs.values_list('id', flat=True))

    # Project scope: global (project=None) OR matching project
    from django.db.models import Q
    if project_id is not None:
        scoped_ids = set(
            RagDocument.objects.filter(
                Q(project__isnull=True) | Q(project_id=project_id),
                ingestion_status='ready',
            ).values_list('id', flat=True)
        )
        if molecule_type and molecule_type != 'undetermined':
            scoped_ids &= ready_doc_ids
        ready_doc_ids = scoped_ids

    chunks = RagChunk.objects.filter(document_id__in=ready_doc_ids).select_related('document')

    # Phase filter applied in Python (JSONField list comparison)
    if phase:
        def _phase_ok(chunk):
            relevance = chunk.document.phase_relevance
            return not relevance or phase in relevance
        chunks = [c for c in chunks if _phase_ok(c)]
    else:
        chunks = list(chunks)

    if not chunks:
        return []

    query_vec = embed(query)
    scored = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        score = _cosine_sim(query_vec, chunk.embedding)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    return [
        {
            'document': chunk.document.name,
            'document_type': chunk.document.document_type,
            'chunk_index': chunk.chunk_index,
            'text': chunk.chunk_text,
            'score': round(score, 4),
        }
        for score, chunk in top
    ]


# ─── Text chunking helpers ───────────────────────────────────────────────────

def _rough_token_count(text: str) -> int:
    """Approximate token count: ~4 chars per token."""
    return max(1, len(text) // 4)


def chunk_text(text: str, chunk_tokens: int = CHUNK_SIZE_TOKENS, overlap_tokens: int = CHUNK_OVERLAP_TOKENS) -> list[str]:
    """Split text into overlapping chunks by approximate token count."""
    words = text.split()
    if not words:
        return []

    # Estimate words per token (~0.75 words/token for English)
    words_per_chunk = max(1, int(chunk_tokens * 0.75))
    words_per_overlap = max(0, int(overlap_tokens * 0.75))
    step = max(1, words_per_chunk - words_per_overlap)

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        chunks.append(' '.join(words[start:end]))
        if end >= len(words):
            break
        start += step

    return chunks


# ─── File extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    """Return (full_text, page_count) from a PDF."""
    import pdfplumber
    pages = []
    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return '\n'.join(pages), page_count


def extract_text_from_docx(file_path: str) -> tuple[str, int]:
    """Return (full_text, approx_page_count) from a DOCX."""
    import docx
    doc = docx.Document(file_path)
    text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    page_count = max(1, _rough_token_count(text) // 375)
    return text, page_count


def extract_text_from_txt(file_path: str) -> tuple[str, int]:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    page_count = max(1, _rough_token_count(text) // 375)
    return text, page_count


def extract_text(file_path: str) -> tuple[str, int]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ('.docx', '.doc'):
        return extract_text_from_docx(file_path)
    else:
        return extract_text_from_txt(file_path)


# ─── Ingest a single document ────────────────────────────────────────────────

def ingest_document(rag_document_id: int) -> bool:
    """Extract, chunk, embed, and save a RagDocument. Returns True on success."""
    from core.models import RagChunk, RagDocument

    try:
        doc = RagDocument.objects.get(id=rag_document_id)
        doc.ingestion_status = 'processing'
        doc.save(update_fields=['ingestion_status'])

        text, page_count = extract_text(doc.file_path)
        doc.page_count = page_count
        doc.save(update_fields=['page_count'])

        chunks_text = chunk_text(text)

        # Delete existing chunks (re-ingest scenario)
        RagChunk.objects.filter(document=doc).delete()

        for i, chunk in enumerate(chunks_text):
            embedding = embed(chunk)
            RagChunk.objects.create(
                document=doc,
                chunk_index=i,
                chunk_text=chunk,
                embedding=embedding,
            )

        doc.ingestion_status = 'ready'
        doc.save(update_fields=['ingestion_status'])
        logger.info(f"Ingested {doc.name}: {len(chunks_text)} chunks from {page_count} pages")
        return True

    except Exception as exc:
        logger.error(f"Failed to ingest RagDocument {rag_document_id}: {exc}", exc_info=True)
        try:
            RagDocument.objects.filter(id=rag_document_id).update(ingestion_status='failed')
        except Exception:
            pass
        return False


def format_rag_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a prompt-ready context block."""
    if not chunks:
        return ""
    parts = ["## Relevant Pharmaceutical References\n"]
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] {chunk['document']} (chunk {chunk['chunk_index']}, score={chunk['score']:.3f})\n{chunk['text']}\n")
    return '\n'.join(parts)

"""
Ingest a directory of pharmaceutical documents into the RAG pipeline.

Usage:
  python manage.py ingest_rag_corpus --corpus-dir /path/to/rag_corpus/
  python manage.py ingest_rag_corpus --corpus-dir /path/to/rag_corpus/ --force   # re-ingest already-ready docs
"""

import os

from django.core.management.base import BaseCommand

from core.models import RagDocument
from core.services.rag import ingest_document

EXTENSION_WHITELIST = {'.pdf', '.docx', '.doc', '.txt'}

# Heuristics for classifying documents by filename
MOLECULE_TYPE_KEYWORDS = {
    'biologic': ['q5', 's6', 'antibody', 'biologic', 'protein', 'mab', 'biosimilar'],
    'small_molecule': ['q6a', 'q3', 'q1', 'q2', 'q8', 'q9', 'q11', 'lipinski', 'admet', 'synthesis', 'small'],
}
PHASE_KEYWORDS = {
    'discovery': ['discovery', 'target', 'disease', 'hit', 'fragment', 'virtual', 'screening'],
    'lead_optimization': ['lead', 'optimization', 'sar', 'admet', 'lipinski', 'mpo'],
    'drug_substance': ['drug_substance', 'synthesis', 'salt', 'polymorph', 'process', 'q11'],
    'drug_product': ['drug_product', 'formulation', 'excipient', 'stability', 'q8'],
    'analytical': ['analytical', 'method', 'validation', 'q2', 'q3'],
    'preclinical': ['preclinical', 'toxicology', 'pk', 'admet', 'm3', 's2', 's7'],
    'regulatory': ['regulatory', 'ind', 'bla', 'nda', 'ich', 'guidance', 'q6'],
}
DOC_TYPE_KEYWORDS = {
    'ich_guideline': ['ich', 'q1', 'q2', 'q3', 'q5', 'q6', 'q8', 'q9', 'q11', 'm3', 's2', 's5', 's6', 's7'],
    'academic_paper': ['lipinski', 'gleeson', 'wager', 'bleicher', 'carter', 'jarasch', 'jain', 'hopkins', 'leeson'],
}


def _classify_document(filename: str) -> dict:
    lower = filename.lower().replace('-', '_').replace(' ', '_')
    name_no_ext = os.path.splitext(lower)[0]

    doc_type = 'other'
    for dtype, keywords in DOC_TYPE_KEYWORDS.items():
        if any(kw in name_no_ext for kw in keywords):
            doc_type = dtype
            break

    mol_type = 'both'
    for mtype, keywords in MOLECULE_TYPE_KEYWORDS.items():
        if any(kw in name_no_ext for kw in keywords):
            mol_type = mtype
            break

    phase_relevance = []
    for phase, keywords in PHASE_KEYWORDS.items():
        if any(kw in name_no_ext for kw in keywords):
            phase_relevance.append(phase)

    return {'document_type': doc_type, 'molecule_type': mol_type, 'phase_relevance': phase_relevance}


class Command(BaseCommand):
    help = 'Ingest a directory of pharmaceutical documents into the RAG pipeline'

    def add_arguments(self, parser):
        parser.add_argument('--corpus-dir', required=True, help='Path to directory containing documents')
        parser.add_argument('--force', action='store_true', help='Re-ingest documents that are already ready')

    def handle(self, *args, **options):
        corpus_dir = options['corpus_dir']
        force = options['force']

        if not os.path.isdir(corpus_dir):
            self.stderr.write(self.style.ERROR(f"Directory not found: {corpus_dir}"))
            return

        files = []
        for root, _, filenames in os.walk(corpus_dir):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in EXTENSION_WHITELIST:
                    files.append(os.path.join(root, filename))

        self.stdout.write(f"Found {len(files)} documents in {corpus_dir}")

        ingested = 0
        skipped = 0
        failed = 0

        for file_path in files:
            filename = os.path.basename(file_path)
            doc_name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')

            existing = RagDocument.objects.filter(file_path=file_path).first()
            if existing and existing.ingestion_status == 'ready' and not force:
                self.stdout.write(f"  SKIP (already ready): {filename}")
                skipped += 1
                continue

            classification = _classify_document(filename)

            if existing:
                doc = existing
                doc.ingestion_status = 'pending'
                doc.save(update_fields=['ingestion_status'])
            else:
                doc = RagDocument.objects.create(
                    name=doc_name,
                    file_path=file_path,
                    uploaded_by='system',
                    **classification,
                )

            self.stdout.write(f"  Ingesting: {filename} (type={classification['document_type']}, mol={classification['molecule_type']})...")
            success = ingest_document(doc.id)
            if success:
                ingested += 1
                chunk_count = doc.chunks.count()
                self.stdout.write(self.style.SUCCESS(f"    OK — {chunk_count} chunks"))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f"    FAILED"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Ingested: {ingested}, Skipped: {skipped}, Failed: {failed}"
            )
        )

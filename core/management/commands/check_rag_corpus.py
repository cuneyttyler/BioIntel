"""
Print a summary of the RAG corpus status.

Usage:
  python manage.py check_rag_corpus
"""

from django.core.management.base import BaseCommand

from core.models import RagChunk, RagDocument


class Command(BaseCommand):
    help = 'Print a summary of the RAG corpus status'

    def handle(self, *args, **options):
        total_docs = RagDocument.objects.count()
        total_chunks = RagChunk.objects.count()

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"RAG Corpus Status")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Total documents : {total_docs}")
        self.stdout.write(f"Total chunks    : {total_chunks}")
        self.stdout.write("")

        for status in ('ready', 'processing', 'pending', 'failed'):
            docs = RagDocument.objects.filter(ingestion_status=status)
            count = docs.count()
            if count:
                label = self.style.SUCCESS(status) if status == 'ready' else self.style.WARNING(status)
                self.stdout.write(f"  {status:12s}: {count} documents")
                for doc in docs:
                    chunk_count = doc.chunks.count()
                    self.stdout.write(f"    - {doc.name[:60]} ({doc.document_type}, {doc.molecule_type}) — {chunk_count} chunks")

        self.stdout.write(f"{'='*60}\n")

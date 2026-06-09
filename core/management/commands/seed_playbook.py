"""
Ingest the bundled pharmaceutical playbook from core/data/playbook/ into the RAG pipeline.

Usage:
  python manage.py seed_playbook
  python manage.py seed_playbook --force   # re-ingest even if already ready
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Ingest the bundled pharmaceutical playbook corpus into the RAG pipeline'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Re-ingest documents already marked ready')

    def handle(self, *args, **options):
        playbook_dir = os.path.join(settings.BASE_DIR, 'core', 'data', 'playbook')

        if not os.path.isdir(playbook_dir):
            self.stderr.write(
                self.style.WARNING(
                    f"Playbook directory not found: {playbook_dir}\n"
                    "Create the directory and add ICH guidelines + academic papers as PDFs."
                )
            )
            return

        self.stdout.write(f"Seeding playbook from {playbook_dir}")
        force_flag = ['--force'] if options['force'] else []
        call_command('ingest_rag_corpus', corpus_dir=playbook_dir, force=options['force'])

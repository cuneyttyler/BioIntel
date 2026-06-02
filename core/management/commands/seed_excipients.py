import csv
import json
import os
from django.core.management.base import BaseCommand
from core.models import Excipient


class Command(BaseCommand):
    help = "Seed the Excipient table from core/data/excipients.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'excipients.csv'),
            help='Path to excipients CSV file',
        )

    def handle(self, *args, **options):
        csv_path = os.path.abspath(options['file'])
        if not os.path.exists(csv_path):
            self.stderr.write(f"File not found: {csv_path}")
            return

        created = 0
        skipped = 0

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('name', '').strip()
                if not name:
                    continue

                try:
                    iig_limit = float(row['iig_limit']) if row.get('iig_limit', '').strip() else None
                except (ValueError, TypeError):
                    iig_limit = None

                try:
                    incompat_raw = row.get('incompatibilities', '[]').strip()
                    incompatibilities = json.loads(incompat_raw) if incompat_raw else []
                except (json.JSONDecodeError, ValueError):
                    incompatibilities = []

                gras_raw = row.get('gras_status', '').strip().lower()
                gras_status = True if gras_raw == 'true' else (False if gras_raw == 'false' else None)

                _, was_created = Excipient.objects.get_or_create(
                    name=name,
                    defaults={
                        'iig_limit': iig_limit,
                        'iig_unit': row.get('iig_unit', '').strip(),
                        'function': row.get('function', '').strip(),
                        'route': row.get('route', '').strip(),
                        'gras_status': gras_status,
                        'incompatibilities': incompatibilities,
                        'notes': row.get('notes', '').strip(),
                    },
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done: {created} excipients created, {skipped} already existed.")
        )

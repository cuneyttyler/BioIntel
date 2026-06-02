from django.db import migrations, models


class Migration(migrations.Migration):
    """
    The old SaltScreenCandidate had hygroscopicity (CharField NOT NULL, no default).
    The field was removed from the model but the column still exists in the DB.
    Since Django no longer includes it in INSERTs, SQLite enforces NOT NULL and fails.
    Give it a blank default so the DB column is satisfied without the ORM touching it.
    """

    dependencies = [
        ('core', '0008_salt_candidate_counterion_nullable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saltscreencandidate',
            name='hygroscopicity',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_stability_result_extra_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='specification',
            name='criteria_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('NMT', 'NMT (Not More Than)'),
                    ('NLT', 'NLT (Not Less Than)'),
                    ('between', 'Between (Range)'),
                    ('conforms', 'Conforms To'),
                    ('report', 'Report Only'),
                ],
                default='NMT',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='specification',
            name='spec_type',
            field=models.CharField(
                choices=[
                    ('release', 'Release'),
                    ('shelf_life', 'Shelf Life'),
                    ('in_process', 'In-Process'),
                    ('raw_material', 'Raw Material'),
                ],
                default='release',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='specification',
            name='acceptance_criteria',
            field=models.CharField(max_length=500),
        ),
    ]

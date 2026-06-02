from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_specification_criteria_type_raw_material'),
    ]

    operations = [
        migrations.AddField(
            model_name='preclinicalstudy',
            name='title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='preclinicalstudy',
            name='glp',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='preclinicalstudy',
            name='primary_endpoints',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='preclinicalstudy',
            name='success_criteria',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='preclinicalstudy',
            name='results_summary',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='preclinicalstudy',
            name='conclusion',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='preclinicalstudy',
            name='noael_mgkg',
            field=models.FloatField(blank=True, null=True),
        ),
    ]

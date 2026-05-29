import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_synthesisplan_and_project_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='synthesisplan',
            name='analog_candidate',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='synthesis_plans',
                to='core.analogcandidate',
            ),
        ),
        migrations.AddConstraint(
            model_name='synthesisplan',
            constraint=models.UniqueConstraint(
                condition=models.Q(analog_candidate__isnull=False),
                fields=['analog_candidate', 'plan_type'],
                name='unique_plan_type_per_analog',
            ),
        ),
    ]

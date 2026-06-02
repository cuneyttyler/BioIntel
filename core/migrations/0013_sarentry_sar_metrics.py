from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_preclinicalstudy_extended_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='sarentry',
            name='logp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sarentry',
            name='mw',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sarentry',
            name='selectivity_value',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sarentry',
            name='selectivity_target',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]

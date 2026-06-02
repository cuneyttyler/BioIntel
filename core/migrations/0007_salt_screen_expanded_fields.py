from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_analog_candidate_selected'),
    ]

    operations = [
        # SaltPolymorphScreen new fields
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='objective',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='baseline_pka',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='baseline_melting_point_c',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='baseline_hygroscopicity',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='baseline_solubility_mgml',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='baseline_logp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='baseline_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='selection_rationale',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='saltpolymorphscreen',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # SaltScreenCandidate — add new fields, keep old ones
        migrations.AddField(
            model_name='saltscreencandidate',
            name='name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='saltscreencandidate',
            name='cas_number',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='saltscreencandidate',
            name='counterion_type',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='saltscreencandidate',
            name='pka_delta',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='saltscreencandidate',
            name='theoretical_solubility_impact',
            field=models.CharField(default='unknown', max_length=20),
        ),
        migrations.AddField(
            model_name='saltscreencandidate',
            name='notes',
            field=models.TextField(blank=True),
        ),

        # SaltScreenExperiment — add granular result fields, make old fields optional
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='prep_method',
            field=models.CharField(blank=True, default='slurry', max_length=20),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='solvent',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='ratio',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='temperature_c',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='results_xrpd',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='results_dsc',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='results_tga',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='results_solubility',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='results_appearance',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='saltscreenexperiment',
            name='observed_form',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='saltscreenexperiment',
            name='method',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]

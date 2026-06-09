from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_app_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='tpp_data',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

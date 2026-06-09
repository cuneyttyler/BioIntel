from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_panel_session_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiplanstep',
            name='suggested_actions',
            field=models.JSONField(default=list),
        ),
    ]

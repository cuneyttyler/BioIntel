from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_salt_screen_expanded_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saltscreencandidate',
            name='counterion_or_polymorph',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]

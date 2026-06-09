from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_v3_project_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(
                    choices=[
                        ('claude', 'Claude (Anthropic)'),
                        ('openai', 'OpenAI'),
                        ('mistral', 'Mistral'),
                        ('custom', 'Custom Endpoint'),
                    ],
                    default='claude',
                    max_length=20,
                )),
                ('model', models.CharField(default='claude-sonnet-4-6', max_length=100)),
                ('anthropic_api_key', models.CharField(blank=True, max_length=500)),
                ('openai_api_key', models.CharField(blank=True, max_length=500)),
                ('mistral_api_key', models.CharField(blank=True, max_length=500)),
                ('custom_endpoint', models.CharField(blank=True, max_length=500)),
                ('custom_api_key', models.CharField(blank=True, max_length=500)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'App Settings',
            },
        ),
    ]

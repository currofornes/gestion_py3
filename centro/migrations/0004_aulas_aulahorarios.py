# Generated by Django 4.2.7 on 2024-10-25 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0003_cursos_dificultad'),
    ]

    operations = [
        migrations.AddField(
            model_name='aulas',
            name='AulaHorarios',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]

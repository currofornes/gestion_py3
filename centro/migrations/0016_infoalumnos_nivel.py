# Generated by Django 4.2.7 on 2025-01-06 21:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0015_alter_centros_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='infoalumnos',
            name='Nivel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='InfoNivel', to='centro.niveles'),
        ),
    ]

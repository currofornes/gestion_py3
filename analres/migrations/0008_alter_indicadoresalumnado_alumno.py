# Generated by Django 4.2.7 on 2025-01-15 21:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0018_alter_infoalumnos_alumno'),
        ('analres', '0007_alter_indicadoresalumnado_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicadoresalumnado',
            name='Alumno',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='indicadores', to='centro.alumnos'),
        ),
    ]

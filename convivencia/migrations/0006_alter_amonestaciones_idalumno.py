# Generated by Django 4.2.7 on 2025-01-15 22:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0018_alter_infoalumnos_alumno'),
        ('convivencia', '0005_remove_propuestassancion_ultima_amonestacion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amonestaciones',
            name='IdAlumno',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='amonestaciones', to='centro.alumnos'),
        ),
    ]
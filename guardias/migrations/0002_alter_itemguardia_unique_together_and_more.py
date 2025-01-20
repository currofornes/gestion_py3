# Generated by Django 4.2.7 on 2025-01-16 16:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0018_alter_infoalumnos_alumno'),
        ('guardias', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='itemguardia',
            unique_together={('Unidad', 'ProfesorAusente', 'Aula', 'Tarea', 'Materia', 'Fecha', 'Tramo', 'ProfesorNotifica', 'ProfesorConfirma', 'curso_academico')},
        ),
        migrations.AlterUniqueTogether(
            name='tiempoguardia',
            unique_together={('profesor', 'dia_semana', 'tramo', 'tiempo_asignado', 'item_guardia', 'curso_academico')},
        ),
    ]
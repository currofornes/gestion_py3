# Generated by Django 4.2.7 on 2025-01-20 11:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0018_alter_infoalumnos_alumno'),
        ('tde', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='incidenciastic',
            unique_together={('profesor', 'aula', 'prioridad', 'comentario', 'curso_academico')},
        ),
    ]
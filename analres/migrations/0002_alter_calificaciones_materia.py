# Generated by Django 4.2.7 on 2024-12-28 13:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0010_alter_materias_finalvigencia'),
        ('analres', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calificaciones',
            name='Materia',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='centro.materias'),
        ),
    ]

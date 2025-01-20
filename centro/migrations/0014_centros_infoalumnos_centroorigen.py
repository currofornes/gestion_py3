# Generated by Django 4.2.7 on 2025-01-03 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('centro', '0013_infoalumnos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Centros',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Codigo', models.CharField(blank=True, max_length=8, null=True)),
                ('Nombre', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Centro',
                'verbose_name_plural': 'Centros',
            },
        ),
        migrations.AddField(
            model_name='infoalumnos',
            name='CentroOrigen',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='centro.centros'),
        ),
    ]
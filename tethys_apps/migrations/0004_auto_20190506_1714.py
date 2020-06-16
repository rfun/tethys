# Generated by Django 2.1.8 on 2019-05-06 17:14

import django.contrib.postgres.fields
from django.db import migrations, models

feedback_emails_data = {}


def data_export(apps, schema_editor):
    TethysApp = apps.get_model('tethys_apps', 'TethysApp')

    for o in TethysApp.objects.raw('SELECT * FROM tethys_apps_tethysapp'):
        feedback_emails_data[o.id] = o.feedback_emails

def data_import(apps, schema_editor):
    TethysApp = apps.get_model('tethys_apps', 'TethysApp')


    for id, values in feedback_emails_data.items():
        o = TethysApp.objects.get(id=id)
        o.feedback_emails = values
        o.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tethys_apps', '0003_python3_compatibility'),
    ]

    operations = [
        migrations.RunPython(data_export),
        # Remove fields to clear data
        migrations.RemoveField(
            model_name='tethysapp',
            name='feedback_emails',
        ),
        migrations.AddField(
            model_name='tethysapp',
            name='feedback_emails',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=200, null=True), default=list, size=None),
        ),
        migrations.RunPython(data_import),
    ]

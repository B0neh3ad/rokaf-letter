# Generated by Django 5.0.2 on 2024-02-10 09:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_rename_reserved_date_letter_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='letter',
            old_name='date',
            new_name='sent_date',
        ),
    ]

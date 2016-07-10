# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0055_userprofile_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='old_problem_name',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]

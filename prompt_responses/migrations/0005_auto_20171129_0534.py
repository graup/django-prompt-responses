# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-29 11:34
from __future__ import unicode_literals

from django.db import migrations
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('prompt_responses', '0004_auto_20171113_0234'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prompt',
            name='prompt_set',
        ),
        migrations.AddField(
            model_name='promptset',
            name='prompts',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='prompt_responses.Prompt'),
        ),
    ]

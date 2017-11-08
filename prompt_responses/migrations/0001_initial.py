# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-08 11:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Prompt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[(b'likert', 'likert'), (b'openended', 'open-ended'), (b'tagging', 'tagging')], default=b'likert', max_length=20)),
                ('scale', models.PositiveIntegerField(blank=True, null=True, verbose_name='maximum value of likert scale')),
                ('text', models.TextField(default=b'{object}', verbose_name='text, format can contain {object}')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('prompt_object_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prompts_as_prompt', to='contenttypes.ContentType', verbose_name='type of objects contained in prompt')),
            ],
        ),
        migrations.CreateModel(
            name='PromptSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.SlugField()),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('rating', models.IntegerField(blank=True, null=True, verbose_name='rating response')),
                ('text', models.TextField(blank=True, null=True, verbose_name='text response')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('prompt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='prompt_responses.Prompt')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(default=0, verbose_name='rating')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='prompt_responses.Response')),
            ],
        ),
        migrations.AddField(
            model_name='prompt',
            name='prompt_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prompts', to='prompt_responses.PromptSet'),
        ),
        migrations.AddField(
            model_name='prompt',
            name='response_object_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prompts_as_response', to='contenttypes.ContentType', verbose_name='type of objects available for responses'),
        ),
    ]

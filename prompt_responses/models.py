# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Count, Avg, F, Max
from random import randint


class PromptSet(models.Model):
    created = AutoCreatedField(_('created'))
    modified = AutoLastModifiedField(_('modified'))
    name = models.SlugField()


class Prompt(models.Model):
    TYPES = Choices(
        ('likert', _('likert')),
        ('openended', _('open-ended')),
        ('tagging', _('tagging'))
    )

    type = models.CharField(choices=TYPES, default=TYPES.likert, max_length=20)
    scale = models.PositiveIntegerField(_('maximum value of likert scale'), null=True, blank=True)
    text = models.TextField(_('text, format can contain {object}'), default="{object}")

    prompt_object_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('type of objects contained in prompt'),
        null=True, blank=True, related_name='prompts_as_prompt'
    )
    response_object_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('type of objects available for responses'),
        null=True, blank=True, related_name='prompts_as_response'
    )

    created = AutoCreatedField(_('created'))
    modified = AutoLastModifiedField(_('modified'))
    prompt_set = models.ForeignKey(
        'PromptSet',
        on_delete=models.CASCADE,
        related_name='prompts',
        null=True, blank=True
    )

    def display_text(self, instance=None):
        return self.text.format(object=instance)

    def __str__(self):
        return self.text

    class Instance(object):
        def __init__(self, prompt, obj, response_objects=None):
            self.prompt = prompt
            self.object = obj
            self.response_objects = response_objects

        def __str__(self):
            return self.prompt.display_text(self.object)
    
    def get_queryset(self):
        return self.prompt_object_type.model_class().objects

    def get_response_queryset(self):
        return self.response_object_type.model_class().objects
    
    def get_prompt_object(self):
        """Get one object from the queryset to display in prompt"""
        queryset = self.get_queryset()

        count = queryset.aggregate(count=Count('id'))['count']
        random_index = randint(0, count - 1)
        return queryset.all()[random_index]

    def get_response_objects(self):
        """Get a number of objects to display in tagging prompt"""
        queryset = self.get_response_queryset()
        N = 3
        return queryset.all()[0:N]

    def get_instance(self):
        """Creates a single instance of this prompt with populated object"""
        obj = self.get_prompt_object()
        response_objects = None
        if self.type == self.TYPES.tagging:
            response_objects = self.get_response_objects()
        return self.__class__.Instance(self, obj, response_objects)

    def create_response(self, user, tags=None, **kwargs):
        """
        Create and save a new response for this prompt.
        Pass rating, text, or prompt_object as needed.
        To save tag responses, pass tags=[(object1, rating1), (object2, rating2), ...]

        Simple responses are not automatically unique per user
        (some experiments might require asking the same question multiple times).
        Some of the analytics functions offer a user_unique parameter to restrict analysis
        to the user's latest response only.

        In contrast, note that tag responses are ensured to be unique
        for (prompt, user, prompt_object, response_object). If the user tagged this 
        combination before, it will be updated, incl. its relation
        (i.e. the original Response object will no longer be associated with this tag).
        """
        response = Response(**kwargs)
        response.user = user
        response.prompt = self
        response.save()
        if tags:
            for tag_object, tag_rating in tags:
                try:
                    # Try to get existing tag by this user
                    tag = Tag.objects.get(
                        response__prompt=self,
                        response__user=user,
                        response__object_id=response.prompt_object.id,
                        response__content_type=ContentType.objects.get_for_model(response.prompt_object),
                        object_id=tag_object.id,
                        content_type=ContentType.objects.get_for_model(tag_object),
                    )
                    tag.rating = tag_rating
                    tag.save()
                    response.tags.add(tag)
                except Tag.DoesNotExist:
                    response.tags.create(response_object=tag_object, rating=tag_rating)
        return response

    def get_response_count(self, user_unique=True):
        """
        Get the count of all responses to this prompt.
        : user_unique (default True) only count each user's latest response
        """
        q = self.responses
        if user_unique:
            # Group by user
            q = q.values('user').annotate(count=Count('user')).order_by('user')
        return q.count()

    def get_mean_rating(self, user_unique=True):
        """
        Get the mean rating of all responses to this prompt.
        : user_unique (default True) only count each user's latest response
        """
        q = self.responses
        if user_unique:
            # Select most recent ratings for each user
            latest_ratings = q.order_by().values('user_id').annotate(
                max_id=Max('id')
            ).values('max_id')
            q = q.filter(pk__in=latest_ratings)
        r = q.aggregate(average_rating=Avg('rating'))
        return r['average_rating']

    def get_mean_tag_ratings(self, prompt_object):
        """
        Get mean ratings for all response_objects of prompt_object
        Returns <QuerySet [{'response_object_id': 1, 'average_rating': -1.0}, ...>
        """
        # SELECT AVG(tags__rating) WHERE prompt_object=... AND prompt_id=... GROUP BY(response_object)
        q = self.responses

        q = q.values(response_object_id=F('tags__object_id')).filter(
            object_id=prompt_object.id, content_type=ContentType.objects.get_for_model(prompt_object),
        )
        q = q.annotate(average_rating=Avg('tags__rating'))
        return q
    
    def get_mean_tag_rating(self, prompt_object, response_object):
        """Get mean rating for response_object of prompt_object"""
        # SELECT AVG(tags__rating) WHERE prompt_object=... AND response_object=... AND prompt_id=...
        q = self.responses
            
        q = q.filter(
            object_id=prompt_object.id, content_type=ContentType.objects.get_for_model(prompt_object),
            tags__object_id=response_object.id, tags__content_type=ContentType.objects.get_for_model(response_object),
        )
        
        r = q.aggregate(average_rating=Avg('tags__rating'))        
        return r['average_rating']


class Response(models.Model):
    created = AutoCreatedField(_('created'))
    prompt = models.ForeignKey(
        'Prompt',
        on_delete=models.CASCADE,
        related_name='responses'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    rating = models.IntegerField(_('rating response'), null=True, blank=True)
    text = models.TextField(_('text response'), null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    prompt_object = GenericForeignKey('content_type', 'object_id')


class Tag(models.Model):
    response = models.ForeignKey(
        'Response',
        on_delete=models.CASCADE,
        related_name='tags'
    )
    rating = models.IntegerField(_('rating'), default=0)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    response_object = GenericForeignKey('content_type', 'object_id')

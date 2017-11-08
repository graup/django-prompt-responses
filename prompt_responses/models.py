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
from collections import defaultdict
from django.db import transaction


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

    @classmethod
    def create(cls, **kwargs):
        """Convenience method that automatically gets the ContentType objects for passed in model classes"""
        if kwargs.get('prompt_object_type', None):
            if not isinstance(kwargs['prompt_object_type'], ContentType):
                kwargs['prompt_object_type'] = ContentType.objects.get_for_model(kwargs['prompt_object_type'])
        if kwargs.get('response_object_type', None):
            if not isinstance(kwargs['response_object_type'], ContentType):
                kwargs['response_object_type'] = ContentType.objects.get_for_model(kwargs['response_object_type'])
        return cls.objects.create(**kwargs)

    class Instance(object):
        """
        An instance of a prompt to be rendered by UI.
        It has `object` and `response_objects` that can be populated into the `prompt`.
        `str(instance)` returns the prompt text with the inserted `object`.
        """
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
        # Todo: make algorithm here plugable
        count = queryset.aggregate(count=Count('id'))['count']
        random_index = randint(0, count - 1)
        return queryset.all()[random_index]

    def get_response_objects(self):
        """Get a number of objects to display in tagging prompt"""
        queryset = self.get_response_queryset()
        # Todo: make algorithm here plugable
        N = 3
        return queryset.all()[0:N]

    def get_instance(self):
        """Creates a single instance of this prompt with populated object"""
        obj = None
        response_objects = None

        if self.prompt_object_type:
            obj = self.get_prompt_object()
        if self.type == self.TYPES.tagging and self.response_object_type:
            response_objects = self.get_response_objects()

        return self.__class__.Instance(self, obj, response_objects)

    @transaction.atomic
    def create_response(self, user, tags=None, **kwargs):
        """
        Create and save a new response for this prompt.
        Pass rating or text, and prompt_object as needed.
        To save tag responses, pass tags=[(object1, rating1), (object2, rating2), ...]

        Responses per se are not unique per user
        (as some experiments might require asking the same question multiple times).
        Some of the analytics functions offer a `user_unique` parameter to restrict analysis
        to the user's latest response only.

        In contrast, note that tags are ensured to be unique
        for (prompt, user, prompt_object, response_object). If the user tagged this 
        combination before, it will be updated, incl. its relation
        (i.e. the original Response object will no longer be associated with this tag).

        This method verifies that the objects match the models defined in the prompt and
        raises a ValueError on a mismatch.
        """
        prompt_object = kwargs.get('prompt_object', None)
        if prompt_object:
            if ContentType.objects.get_for_model(prompt_object) != self.prompt_object_type:
                msg = 'prompt_object has a different model class (%s) than defined in the prompt (%s)'
                raise ValueError(msg % (prompt_object.__class__.__name__, self.prompt_object_type.model))

        response = Response(**kwargs)
        response.user = user
        response.prompt = self
        response.save()
        if tags:
            for tag_object, tag_rating in tags:
                if ContentType.objects.get_for_model(tag_object) != self.response_object_type:
                    msg = 'tag_object has a different model class (%s) than defined in the prompt (%s)'
                    raise ValueError(msg % (tag_object.__class__.__name__, self.response_object_type.model))
                
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

    def get_mean_tag_rating_matrix(self):
        """
        Get mean ratings for all response_objects of all prompt_objects
        Returns a matrix in the form of a two-level dict
        {object1: {object2: 1}}, ...
        Refer to Django's contenttypes documentation to convert the keys back to model instances,
        e.g. prompt.response_object_type.get_object_for_this_type(pk=object1)
        or prompt.prompt_object_type.get_object_for_this_type(pk=object2)
        """
        # SELECT AVG(tags__rating) WHERE prompt_id=... GROUP BY prompt_object, response_object
        q = Tag.objects.values(
            'response__content_type', 'response__object_id', 
            'content_type', 'object_id'
        ).filter(response__prompt=self).annotate(average_rating=Avg('rating')).order_by('content_type','object_id')

        # Convert rows into matrix
        matrix = defaultdict(dict)
        for row in q.all():
            #right_key = '%d_%d' % (row['content_type'], row['object_id'])
            right_key = row['object_id']
            #left_key = '%d_%d' % (row['response__content_type'], row['response__object_id'])
            left_key = row['response__object_id']
            matrix[left_key][right_key] = row['average_rating']
        
        return dict(matrix)
        
    def get_mean_tag_ratings(self, prompt_object):
        """
        Get mean ratings for all response_objects of prompt_object
        Returns <QuerySet [{'response_object_id': 1, 'average_rating': -1.0}, ...>
        """
        # SELECT AVG(tags__rating) WHERE prompt_object=... AND prompt_id=... GROUP BY response_object
        q = self.responses

        # .values(response_object_id=F('tags__object_id'))
        q = q.annotate(response_object_id=F('tags__object_id')).values('response_object_id').filter(
            object_id=prompt_object.id, content_type=ContentType.objects.get_for_model(prompt_object),
        )
        q = q.annotate(average_rating=Avg('tags__rating'))
        return q
    
    def get_mean_tag_rating(self, prompt_object, response_object):
        """Get mean rating for response_object of prompt_object across all users"""
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

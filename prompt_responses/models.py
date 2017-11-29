# -*- coding: utf-8 -*-

from django.db import models, transaction
from django.db.models import Count, Avg, F, Max
from model_utils import Choices, FieldTracker
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.utils.html import html_safe
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
import random
from collections import defaultdict
from sortedm2m.fields import SortedManyToManyField

class PromptSet(models.Model):
    created = AutoCreatedField(_('created'))
    modified = AutoLastModifiedField(_('modified'))
    name = models.SlugField()
    prompts = SortedManyToManyField('Prompt')

    @property
    def first_prompt(self):
        return self.prompts.first()

    def __str__(self):
        return self.name


class Prompt(models.Model):
    TYPES = Choices(
        ('likert', _('likert')),
        ('openended', _('open-ended')),
        ('tagging', _('tagging'))
    )

    type = models.CharField(choices=TYPES, default=TYPES.likert, max_length=20)
    scale_min = models.IntegerField(_('minimum value of likert scale'), default=1, blank=True)
    scale_max = models.IntegerField(_('maximum value of likert scale'), null=True, blank=True)
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

    tracker = FieldTracker()

    def display_text(self, instance=None):
        return self.text.format(object=instance)

    def __str__(self):
        return self.text

    custom_scale = None

    def generate_scale(self):
        """
        Returns an iterator suitable for a form field's choices attribute
        to generate a list of rating options for responses to this prompt.
        By default, returns a numeric scale from scale_min to scale_max with
        analogous text labels.
        To change the scale, either subclass Prompt and override this function
        or provide a custom_scale argument to the get_instance() function
        or set the custom_scale attribute of the prompt object.
        custom_scale can be a list or a function that receives one argument, the prompt.
        """
        if self.custom_scale:
            if callable(self.custom_scale):
                return self.custom_scale(self)
            else:
                return self.custom_scale

        low = getattr(self, 'scale_min', 1)
        high = getattr(self, 'scale_max', 5)
        return [(i, str(i)) for i in range(low, high+1)]

    def clean_fields(self, exclude=None):
        super(Prompt, self).clean_fields(exclude=exclude)
        # Check consonsitency between fields
        if self.type in (self.TYPES.tagging, self.TYPES.likert, ):
            if not self.scale_max and not (exclude and 'scale_max' in exclude):
                msg = _('Likert-style and tagging prompts require setting both scale attribute.')
                raise ValidationError({'scale_max': msg})

        if self.type == self.TYPES.tagging:
            if not self.prompt_object_type or not self.response_object_type:
                msg = _('Tagging-style prompts require setting both prompt_object_type and response_object_type attributes.')
                error = {}
                if not self.prompt_object_type:
                    error['prompt_object_type'] = msg
                if not self.response_object_type:
                    error['response_object_type'] = msg
                raise ValidationError(error)
        
        if not self.type == self.TYPES.tagging and self.response_object_type:
                msg = _('Only tagging-style prompts can have a prompt_object_type.')
                raise ValidationError({'response_object_type': msg})

        if self.tracker.has_changed('type'):
            if self.responses.count() > 0:
                msg = _(
                    'Changing type for prompts that have responses is dangerous. '
                    'Please create a new prompt or delete this prompt\'s responses first.'
                )
                raise ValidationError({'type': msg})


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

    @html_safe
    @python_2_unicode_compatible
    class Instance(object):
        """
        A one-off instance of a prompt to be rendered by UI.
        It has `object` and `response_objects` that can be populated into the `prompt`.
        `str(instance)` returns the prompt text with the inserted `object`.
        Objects of this class can be directly printed in HTML templates.
        """
        def __init__(self, prompt, obj, response_objects=None, promptset=None):
            self.prompt = prompt
            self.object = obj
            self.response_objects = response_objects
            self.promptset = promptset

        def __str__(self):
            return self.prompt.display_text(self.object)

        @property
        def prompt_id(self):
            return getattr(self.prompt, 'id', None)
    
        @property
        def next_prompt(self):
            "Get the next prompt in order of the promptset"
            if not self.promptset:
                return None

            # Grab the current prompt's sort_value from the through table
            current_sort_value = self.promptset.prompts.through.objects.extra(
                select={'sort_value': 'sort_value'}
            ).values('sort_value').filter(prompt_id=self.prompt.pk)

            try:
                # Get the prompt with a sort_value > current prompt's sort_value
                prompt_id = self.promptset.prompts.through.objects.filter(sort_value__gt=current_sort_value).values('prompt_id')[0]['prompt_id']
            except IndexError:
                return None
            
            return Prompt.objects.get(pk=prompt_id)
    
    def get_queryset(self):
        """Get the queryset to sample a prompt_object from"""
        return self.prompt_object_type.model_class().objects

    def get_response_queryset(self):
        """Get the queryset to sample response_objects from"""
        return self.response_object_type.model_class().objects
    
    def get_object(self, **kwargs):
        """
        Get one object from the queryset to display in prompt.
        By default this samples one random object from the queryset."""
        queryset = self.get_queryset()
        # Todo: make algorithm here plugable
        count = queryset.aggregate(count=Count('id'))['count']
        random_index = random.randint(0, count - 1)
        return queryset.all()[random_index]

    def get_response_objects(self, n=3, **kwargs):
        """
        Get a number of objects to display in tagging prompt.
        By default this selects n=3 random objects from the queryset
        call get_instance with n=5 to choose other numbers.
        """
        queryset = self.get_response_queryset()
        # Todo: make algorithm here plugable
        count = queryset.aggregate(count=Count('id'))['count']
        sample = random.sample(range(0, count), min(n, count))
        return [queryset.all()[idx] for idx in sample]

    def get_instance(self, custom_scale=None, promptset=None, **kwargs):
        """
        Creates a single instance of this prompt with populated object.
        kwargs are passed to get_object() and get_response_objects() so
        you can override these with custom algorithms.
        If you pass a prompt_set, the instance can determine a next_prompt_instance url."""
        obj = None
        response_objects = None
        
        if custom_scale:
            self.custom_scale = custom_scale

        if self.prompt_object_type:
            obj = self.get_object(**kwargs)
        if self.type == self.TYPES.tagging and self.response_object_type:
            response_objects = self.get_response_objects(**kwargs)

        return self.__class__.Instance(self, obj, response_objects, promptset)

    @transaction.atomic
    def create_response(self, user, tags=None, **kwargs):
        """
        Create and save a new response for this prompt.
        Pass rating or text, and prompt_object as needed.
        To save tag responses, pass tags=[(object1, rating1), (object2, rating2), ...]
        OR as a dictionary, tags=[{'object_id': id1, 'rating': rating2}, ...]

        Responses per se are not unique per user
        (as some experiments might require asking the same question multiple times).
        Some of the analytics functions offer a `user_unique` parameter to restrict analysis
        to the user's latest response only.

        In contrast, note that tags are ensured to be unique
        for (prompt, user, prompt_object, response_object). If the user tagged this 
        combination before, it will be updated, incl. its relation
        (i.e. the original Response object will no longer be associated with this tag).

        This method verifies that the objects match the models defined in the prompt and
        raises a ValidationException on a mismatch.
        """
        if not 'rating' in kwargs and not 'text' in kwargs and not tags:
            msg = 'A response has to include at least one of rating, text, or tags.'
            raise ValidationError(msg)

        response = Response(**kwargs)
        response.user = user
        response.prompt = self
        response.clean_fields()
        response.save()
        if tags:
            if not self.response_object_type:
                msg = 'This prompt does not support tagging. Set type to tagging and choose a response_object_type'
                raise ValidationError({'tag_object': msg})

            if len(tags) and isinstance(tags[0], dict):
                # Alternative tag dict format, translate
                tags = map(dict, tags)
                tags = [(tag['object_id'], tag['rating']) for tag in tags]

            for tag_object, tag_rating in tags:
                # Resuce tag_object that is only an object_id
                if isinstance(tag_object, (int, str)):
                    tag_object = self.response_object_type.get_object_for_this_type(pk=tag_object)

                if ContentType.objects.get_for_model(tag_object) != self.response_object_type:
                    msg = 'tag_object has a different model class (%s) than defined in the prompt (%s)'
                    raise ValidationError({'tag_object': msg % (tag_object.__class__.__name__, self.response_object_type.model)})
                
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

    def clean_fields(self, exclude=None):
        super(Response, self).clean_fields(exclude=exclude)
        # Check type of prompt_object
        if self.prompt_object:
            if ContentType.objects.get_for_model(self.prompt_object) != self.prompt.prompt_object_type:
                msg = 'The Response\'s prompt_object has a different model class (%s) than defined in the prompt (%s)'
                raise ValidationError({'prompt_object': msg % (
                    self.prompt_object.__class__.__name__,
                    self.prompt.prompt_object_type.model
                )})
        
        # Check if reconstruct prompt_object from object_id and prompt object_type
        # This allows to create Response objects with only object_id (making the content_type implicit)
        if not self.prompt_object and self.object_id and self.prompt:
            content_type = self.prompt.prompt_object_type
            self.prompt_object = content_type.get_object_for_this_type(pk=self.object_id)

        # Check if prompt_object is optional
        if not self.prompt_object and self.prompt.prompt_object_type:
            msg = 'This field is required for this prompt.'
            raise ValidationError({'prompt_object': msg})


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

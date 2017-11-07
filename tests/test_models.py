#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-prompt-responses
------------

Tests for `django-prompt-responses` models module.
"""

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from prompt_responses import models
from .models import Book, Category


class TestPrompt_responses(TestCase):

    def setUp(self):
        Book.objects.create(title="Two Scoops of Django")
        self.user = User.objects.create_user(username='alice')
        self.user2 = User.objects.create_user(username='bob')

    def test_basics(self):
        prompt_set = models.PromptSet.objects.create(name='book_rating')
        prompt = models.Prompt.objects.create(
            text="How do you like the book {object}?",
            prompt_object_type=ContentType.objects.get_for_model(Book),
            prompt_set=prompt_set
        )
        instance = prompt.get_instance()
        self.assertEqual(str(instance), 'How do you like the book Two Scoops of Django?')

        response = prompt.create_response(
            user=self.user2,
            prompt_object=instance.object,
            rating=1
        )
        self.assertEqual(response.prompt, prompt)
        self.assertEqual(1, prompt.get_response_count())
        self.assertEqual(1, prompt.get_mean_rating())

        prompt.create_response(
            user=self.user,
            prompt_object=instance.object,
            rating=-1
        )
        self.assertEqual(0, prompt.get_mean_rating())
        
    def test_user_unique(self):
        prompt = models.Prompt.objects.create(
            text="Was {object} a good read?",
            prompt_object_type=ContentType.objects.get_for_model(Book)
        )
        instance = prompt.get_instance()
        response1 = prompt.create_response(
            user=self.user,
            prompt_object=instance.object,
            rating=1
        )
        self.assertEqual(1, prompt.get_response_count(user_unique=True))
        # Create another response for same user
        response2 = prompt.create_response(
            user=self.user,
            prompt_object=instance.object,
            rating=-1
        )
        self.assertEqual(2, prompt.get_response_count(user_unique=False))
        self.assertEqual(1, prompt.get_response_count(user_unique=True))
        self.assertEqual(0, prompt.get_mean_rating(user_unique=False))
        self.assertEqual(-1, prompt.get_mean_rating(user_unique=True))

    def test_tagging_response(self):
        Category.objects.create(name="romance")
        Category.objects.create(name="fantasy")
        Category.objects.create(name="crime")
        Category.objects.create(name="thriller")
        Category.objects.create(name="travel")

        prompt = models.Prompt.objects.create(
            type=models.Prompt.TYPES.tagging,
            text="Please mark all categories that you think are related to {object}.",
            prompt_object_type=ContentType.objects.get_for_model(Book),
            response_object_type=ContentType.objects.get_for_model(Category)
        )
        instance = prompt.get_instance()
        response = prompt.create_response(
            user=self.user,
            prompt_object=instance.object,
            tags=[
                (instance.response_objects[0], -1),
                (instance.response_objects[1], -1),
                (instance.response_objects[2], 1),
            ]
        )
        self.assertEqual(3, models.Tag.objects.count())
        self.assertEqual(-1, prompt.get_mean_tag_rating(instance.object, instance.response_objects[0]))

        prompt.create_response(
            user=self.user2,
            prompt_object=instance.object,
            tags=[
                (instance.response_objects[0], -1),
                (instance.response_objects[1], -1),
                (instance.response_objects[2], -1),
            ]
        )
        self.assertEqual(-1, prompt.get_mean_tag_rating(instance.object, instance.response_objects[0]))
        self.assertEqual(0, prompt.get_mean_tag_rating(instance.object, instance.response_objects[2]))

    def test_tagging_response_unique(self):
        Category.objects.create(name="crime")
        Category.objects.create(name="thriller")
        Category.objects.create(name="travel")

        # Create two response by same user. 
        prompt = models.Prompt.objects.create(
            type=models.Prompt.TYPES.tagging,
            text="Please mark all categories that you think are related to {object}.",
            prompt_object_type=ContentType.objects.get_for_model(Book),
            response_object_type=ContentType.objects.get_for_model(Category)
        )
        instance = prompt.get_instance()
        response1 = prompt.create_response(
            user=self.user,
            prompt_object=instance.object,
            tags=[
                (instance.response_objects[0], 1),
                (instance.response_objects[1], 1),
            ]
        )
        self.assertEqual(2, response1.tags.count())

        # Create another response for same user and prompt, but different tag ratings
        prompt.create_response(
            user=self.user,
            prompt_object=instance.object,
            tags=[
                (instance.response_objects[0], -1),
                (instance.response_objects[2], 0),
            ]
        )

        # Check that original response lost the now updated tag
        self.assertEqual(1, response1.tags.count())
        # there should be 3 tags now (not 4!)
        self.assertEqual(3, models.Tag.objects.filter(response__prompt=prompt).count())

        # Create another unrelated response
        book2 = Book.objects.create(title="Another random book")
        prompt.create_response(
            user=self.user,
            prompt_object=book2,
            tags=[
                (instance.response_objects[0], -1),
                (instance.response_objects[1], -1),
            ]
        )
        # print(prompt.get_mean_tag_ratings(instance.object))

        self.assertEqual(-1, prompt.get_mean_tag_rating(instance.object, instance.response_objects[0]))
        for (index, rating) in enumerate([-1, 1, 0]):
            self.assertEqual(rating, prompt.get_mean_tag_rating(instance.object, instance.response_objects[index]))


    def tearDown(self):
        pass

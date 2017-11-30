#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-prompt-responses
------------

Tests for `django-prompt-responses` models module.
"""

from django.test import TestCase, override_settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

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
        )
        prompt_set.prompts.add(prompt)
        prompt_set.save()
        instance = prompt.get_instance()
        self.assertEqual(str(instance), 'How do you like the book Two Scoops of Django?')
        self.assertEqual(str(prompt), 'How do you like the book {object}?')

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

    def test_passing_model_class(self):
        # These three methods of creating a prompt should all work
        models.Prompt.create(
            text="How do you like the book {object}?",
            prompt_object_type=Book
        )

        models.Prompt.create(
            text="How do you like the book {object}?",
            prompt_object_type=ContentType.objects.get_for_model(Book)
        )

        models.Prompt.objects.create(
            text="How do you like the book {object}?",
            prompt_object_type=ContentType.objects.get_for_model(Book)
        )

        # same for response_object_type
        models.Prompt.create(
            text="How do you like the weather today?",
            response_object_type=Book
        )
        models.Prompt.create(
            text="How do you like the weather today?",
            response_object_type=ContentType.objects.get_for_model(Book)
        )

        
    def test_object_less_prompt(self):
        # prompts without any object type should also work
        prompt = models.Prompt.create(
            text="How do you like the weather today?",
            scale_max=10
        )
        instance = prompt.get_instance()
        prompt.create_response(
            user=self.user,
            rating=10
        )

    def test_user_unique(self):
        prompt = models.Prompt.create(
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

    #@override_settings(DEBUG=True)
    def test_tagging_response(self):
        Category.objects.create(name="romance")
        Category.objects.create(name="fantasy")
        Category.objects.create(name="crime")
        Category.objects.create(name="thriller")
        Category.objects.create(name="travel")

        prompt = models.Prompt.create(
            type=models.Prompt.TYPES.tagging,
            text="Please mark all categories that you think are related to {object}.",
            prompt_object_type=Book,
            response_object_type=Category
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

        ratings = list(prompt.get_mean_tag_ratings(instance.object))
        
        expected = [
            {'response_object_id': instance.response_objects[0].pk, 'average_rating': -1.0},
            {'response_object_id': instance.response_objects[1].pk, 'average_rating': -1.0},
            {'response_object_id': instance.response_objects[2].pk, 'average_rating': 0.0}
        ]
        expected_sorted = sorted(expected, key=lambda k: k['response_object_id']) 

        self.assertEqual(expected_sorted, ratings)

    def test_tagging_response_unique(self):
        Category.objects.create(name="crime")
        Category.objects.create(name="thriller")
        Category.objects.create(name="travel")

        # Create two response by same user. 
        prompt = models.Prompt.create(
            type=models.Prompt.TYPES.tagging,
            text="Please mark all categories that you think are related to {object}.",
            prompt_object_type=Book,
            response_object_type=Category
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

        # Check that all ratings are correct
        for (index, rating) in enumerate([1, 1, None]):
            self.assertEqual(rating, prompt.get_mean_tag_rating(instance.object, instance.response_objects[index]))

        # Create another response for the same user and prompt, but different tag ratings
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

        # Check that all ratings are correct
        self.assertEqual(-1, prompt.get_mean_tag_rating(instance.object, instance.response_objects[0]))
        for (index, rating) in enumerate([-1, 1, 0]):
            self.assertEqual(rating, prompt.get_mean_tag_rating(instance.object, instance.response_objects[index]))

    def test_model_type_checks(self):
        Book.objects.create(title="Two Scoops of Django")
        Category.objects.create(name="crime")
        prompt = models.Prompt.create(
            type=models.Prompt.TYPES.tagging,
            text="Please mark all categories that you think are related to {object}.",
            prompt_object_type=Book,
            response_object_type=Category
        )
        instance = prompt.get_instance()
        # response with wrong prompt_object type
        with self.assertRaises(ValidationError):
            prompt.create_response(
                user=self.user,
                prompt_object=instance.response_objects[0],
                tags=[
                    (instance.object, 1),
                ]
            )
        # response with wrong tag_object type
        with self.assertRaises(ValidationError):
            prompt.create_response(
                user=self.user,
                prompt_object=instance.object,
                tags=[
                    (instance.object, 1),
                ]
            )
        # Check that no response or tags were saved
        self.assertEqual(0, models.Response.objects.count())
        self.assertEqual(0, models.Tag.objects.count())

    def test_tagging_n(self):
        Category.objects.create(name="crime")
        Category.objects.create(name="thriller")
        Category.objects.create(name="travel")
        Category.objects.create(name="children")
        
        prompt = models.Prompt.create(
            type=models.Prompt.TYPES.tagging,
            text="Please mark all categories that you think are related to {object}.",
            prompt_object_type=Book,
            response_object_type=Category
        )
        instance = prompt.get_instance(n=4)
        self.assertEqual(4, len(instance.response_objects))

        instance = prompt.get_instance(n=5)
        # still 4, because there are only 4 items available
        self.assertEqual(4, len(instance.response_objects))
    
    def test_mean_tag_rating_matrix(self):
        prompt = models.Prompt.create(
            type=models.Prompt.TYPES.tagging,
            text="Please mark all categories that you think are related to {object}.",
            prompt_object_type=Book,
            response_object_type=Category
        )
        book1 = Book.objects.create(title="Two Scoops of Django")
        book2 = Book.objects.create(title="Another book")
        Category.objects.create(name="crime")
        Category.objects.create(name="thriller")
        Category.objects.create(name="travel")
        instance = prompt.get_instance()
        prompt.create_response(
            user=self.user,
            prompt_object=book1,
            tags=[
                (instance.response_objects[0], 1),
                (instance.response_objects[1], 1),
                (instance.response_objects[2], -1),
            ]
        )
        prompt.create_response(
            user=self.user,
            prompt_object=book2,
            tags=[
                (instance.response_objects[0], -1),
                (instance.response_objects[1], 0),
                (instance.response_objects[2], 0),
            ]
        )
        prompt.create_response(
            user=self.user2,
            prompt_object=book1,
            tags=[
                (instance.response_objects[0], 0),
                (instance.response_objects[2], 1),
            ]
        )
        prompt.create_response(
            user=self.user2,
            prompt_object=book2,
            tags=[
                (instance.response_objects[1], 1),
                (instance.response_objects[2], -1),
            ]
        )
        expected = {
            book1.pk: {
                instance.response_objects[0].pk: 0.5,
                instance.response_objects[1].pk: 1.0,
                instance.response_objects[2].pk: 0.0
            },
            book2.pk: {
                instance.response_objects[0].pk: -1.0,
                instance.response_objects[1].pk: 0.5,
                instance.response_objects[2].pk: -0.5
            }
        }
        self.assertEqual(expected, prompt.get_mean_tag_rating_matrix())

    def test_promptset_ordering(self):
        prompt_set = models.PromptSet.objects.create(name='book-rating')
        prompt1 = models.Prompt.objects.create(
            text="How do you like the book {object}?",
            prompt_object_type=ContentType.objects.get_for_model(Book),
        )
        prompt_set.prompts.add(prompt1)
        prompt2 = models.Prompt.objects.create(
            text="Is this book written well? {object}",
            prompt_object_type=ContentType.objects.get_for_model(Book),
        )
        prompt_set.prompts.add(prompt2)
        prompt_set.save()

        # prompt set should have first prompt
        prompt = prompt_set.first_prompt
        instance = prompt.get_instance()
        self.assertEquals(instance.next_prompt, None)

        # prompt instance should point to next prompt
        instance = prompt.get_instance(promptset=prompt_set)
        self.assertEquals(instance.prompt.pk, prompt1.pk)
        self.assertEquals(instance.next_prompt.pk, prompt2.pk)

        # next prompt instance should point to None
        next_prompt_instance = instance.next_prompt.get_instance(promptset=prompt_set)
        self.assertEquals(next_prompt_instance.next_prompt, None)

    def tearDown(self):
        pass

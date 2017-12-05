#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-prompt-responses
------------

Tests for `django-prompt-responses` Django Rest Framework compatability.
"""
import json

from django.test import TestCase, override_settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from prompt_responses.models import Prompt, PromptSet
from .models import Book, Category
from prompt_responses.viewsets import PromptViewSet, PromptSetViewSet

class TestPrompt_responses(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='alice')
        self.api = APIRequestFactory()

        Book.objects.create(title="Two Scoops of Django")
        self.prompt = Prompt.create(
            text="How do you like the book {object}?",
            prompt_object_type=Book
        )

    def test_prompt_set(self):        
        prompt_set = PromptSet.objects.create(name='my-prompts')
        prompt1 = Prompt.create(
            text="Prompt number 1",
        )
        prompt2 = Prompt.create(
            text="Prompt number 2",
        )
        prompt3 = Prompt.create(
            text="Prompt number 3",
        )
        prompt_set.prompts.add(prompt1)
        prompt_set.prompts.add(prompt3)
        prompt_set.prompts.add(prompt2)
        prompt_set.save()

        request = self.api.get('')
        view = PromptSetViewSet.as_view({'get': 'retrieve'})
        response = view(request, name='my-prompts').render()
        data = json.loads(response.content.decode('utf8'))
        
        self.assertEquals(data, {
            'url': 'http://testserver/api/prompt-sets/my-prompts/',
            'next_prompt_instance': 'http://testserver/api/prompts/2/instantiate/my-prompts/',
            'ordered_prompts': ['http://testserver/api/prompts/2/', 'http://testserver/api/prompts/4/', 'http://testserver/api/prompts/3/']
        })

    def test_get_prompt(self):
        request = self.api.get('')
        view = PromptViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.prompt.pk).render()
        data = json.loads(response.content.decode('utf8'))
        
        self.assertEquals(data['text'], "How do you like the book {object}?")
        self.assertTrue('url' in data)
        self.assertTrue('instance_url' in data)
    
    def test_get_prompt_instance(self):
        request = self.api.get('')
        view = PromptViewSet.as_view({'get': 'instantiate'})
        response = view(request, pk=self.prompt.pk).render()
        data = json.loads(response.content.decode('utf8'))
        
        self.assertEquals(data['display_text'], "How do you like the book Two Scoops of Django?")
        self.assertEquals(data['response_objects'], None)
        self.assertEquals(self.prompt.id, data['object']['id'])

    def test_create_response(self):
        view = PromptViewSet.as_view({'post': 'create_response'})
        
        prompt_instance = self.prompt.get_instance()

        # Unauthenticated should be not allowed
        request = self.api.post('')
        response = view(request, pk=self.prompt.pk).render()
        self.assertEquals(401, response.status_code)
        
        # Authenticated but Missing data
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.prompt.pk).render()
        self.assertEquals(400, response.status_code)

        # Response with rating but missing prompt_object
        request = self.api.post('', {'rating': 1}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.prompt.pk).render()
        data = json.loads(response.content.decode('utf8'))
        self.assertTrue('prompt_object' in data)
        self.assertEquals(400, response.status_code)

        # Proper rating response
        request = self.api.post('', {
            'rating': 1,
            'object_id': prompt_instance.object.pk
        }, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.prompt.pk).render()
        data = json.loads(response.content.decode('utf8'))
        self.assertEquals(201, response.status_code)
        self.assertEquals(prompt_instance.object.id, data['object_id'])
        self.assertEquals(1, data['rating'])
        
    def test_create_tagging_response(self):
        view = PromptViewSet.as_view({'post': 'create_response'})
        
        Category.objects.create(name="crime")
        Category.objects.create(name="thriller")
        Category.objects.create(name="travel")

        prompt = Prompt.create(
            type=Prompt.TYPES.tagging,
            text="Please rate the relevancy of the following categories for {object}.",
            prompt_object_type=Book,
            response_object_type=Category
        )
        prompt_instance = prompt.get_instance()

        request = self.api.post('', {
            'tags': [{'rating': 5, 'object_id': prompt_instance.response_objects[0].pk}],
            'object_id': prompt_instance.object.pk
        }, format='json')
        force_authenticate(request, user=self.user)
        response = view(request, pk=prompt.pk).render()
        data = json.loads(response.content.decode('utf8'))
        self.assertEquals(201, response.status_code)
        self.assertEquals(prompt_instance.object.id, data['object_id'])
        self.assertEquals(prompt_instance.response_objects[0].pk, data['tags'][0]['object_id'])
        self.assertEquals(5, data['tags'][0]['rating'])


    def tearDown(self):
        pass

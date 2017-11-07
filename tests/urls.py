# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url, include

from prompt_responses.urls import urlpatterns as prompt_responses_urls

urlpatterns = [
    url(r'^', include(prompt_responses_urls, namespace='prompt_responses')),
]

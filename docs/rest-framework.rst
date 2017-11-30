=====================
Django Rest Framework
=====================

To use the included viewsets in your Django Rest Framework API, simply register them
in a router like so:

.. code-block:: python

    from rest_framework import routers
    from prompt_responses.viewsets import PromptViewSet, PromptSetViewSet

    router = routers.DefaultRouter()
    router.register(r'prompts', PromptViewSet)
    router.register(r'prompt-sets', PromptSetViewSet)

    urlpatterns = [
        url(r'^api/', include(router.urls))
    ]

This offers read-only API endpoints for prompts and prompt sets and
one writable endpoint to create responses.

The API endpoints are hyperlinked together, i.e. they return URLs to other resources.
It is recommended to follow these links instead of constructing your own URLs.

Prompt API
----------

**Get a list of all prompts**::

    GET api/prompts/

**Get details about a prompt**::

    GET api/prompts/<prompt_id>/

**Get an instance of a prompt**::

    GET api/prompts/<prompt_id>/instantiate/

**Get an instance of a prompt within the context of a prompt set**::

    GET api/prompts/<prompt_id>/instantiate/<prompt_set_name>/

Create Response API
-------------------

**Save a response for a prompt**::

    POST api/prompts/<prompt_id>/create-response/

This endpoint expects the following data:

TODO

PromptSet API
-------------

**Get a list of all prompt sets**::

    GET api/prompt-sets/

**Get details about a prompt set**::

    GET api/prompt-sets/<prompt_set_name>/

**Traversing an ordered list of prompts**

When you use prompt sets, you can follow the links returned in the responses to
traverse the list of prompts. Both PromptSet and Prompt API responses will
contain a `next_prompt_instance` URL.

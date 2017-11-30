=====
Usage
=====

Admin
-----

This package comes with integration for Django Admin.
It is the easiest way to create new prompts and order them into sets.

In a standard Django installation, the admin views should be automatically registered.

Views
-----

This package includes one view and one mixin you can use to display
prompt instances and create responses.

:doc:`Read more <views>`

Models
------

This package includes four models: Prompt, PromptSet, Response, and Tag.

:doc:`Read more <models>`

Django Rest Framework
---------------------

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

:doc:`Read more <rest-framework>`


=====
Usage
=====

To use prompt_responses in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'prompt_responses.apps.PromptResponsesConfig',
        ...
    )

Add prompt_responses's URL patterns:

.. code-block:: python

    from prompt_responses import urls as prompt_responses_urls


    urlpatterns = [
        ...
        url(r'^', include(prompt_responses_urls)),
        ...
    ]

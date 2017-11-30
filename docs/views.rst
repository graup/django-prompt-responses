=====
Views
=====

Mixins
------

.. class:: PromptInstanceMixin

    Provide prompt and prompt_instance to a view.

    Tries to get prompt by looking up the pk parameter from the request URL.
    Override get_prompt() to choose a different way of obtaining the prompt object.

    Example usage

    .. code-block:: python

       from prompt_responses.views import PromptInstanceMixin

       class MyView(PromptInstanceMixin, View):
            ...

    The view will have both `prompt` and `prompt_instance` as attributes.
    They are also added to the template context.

    .. attribute:: prompt

       The :class:`Prompt` that is displayed in this view

    .. attribute:: prompt_instance

       The :class:`PromptInstance` that is displayed in this view


Class-based Views
-----------------

.. class:: CreateResponseView(PromptInstanceMixin, ...)

    A simple view that can display a template with the instantiated prompt and a form to
    create a response for this prompt.

    You can add it as-is to your URL configuration:

    .. code-block:: python
    
        from prompt_responses.views import CreateResponseView
        
        urlpatterns = [
            url(r'^prompt/(?P<pk>[0-9]+)/$', CreateResponseView.as_view(), name='create_response'),
        ]
    
    Or have a look at the code to get an idea of making your own view.

    For example, you can sub-class `CreateResponseView` and override `get_prompt()`
    to choose a different way of obtaining the prompt object.

    This view requires authentication and uses the user from the current request to create the response.
    You can also use the `BaseCreateResponseView` and provide an alternative `get_user()` method instead.


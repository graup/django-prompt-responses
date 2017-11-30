=====
Views
=====

Mixins
------

.. class:: PromptInstanceMixin:

    Provide prompt and prompt_instance to a view.

    Tries to get prompt by looking up the pk parameter from thr request url.
    Override get_prompt() to choose a different way of obtaining the prompt object.

       from prompt_responses.views import PromptInstanceMixin

       class MyView(PromptInstanceMixin, View):

            ...

                self.prompt
                self.prompt_instance

    Both `prompt` and `prompt_instance` are also added to the template context.


Class-based Views
-----------------

.. class:: CreateResponseView(PromptInstanceMixin, ...):

    A simple view that can display a template with the instantiated prompt and a form to
    create a response for this prompt.

    You can add it as-is to your URL configuration:

        from prompt_responses.views import CreateResponseView
        
        urlpatterns = [
            url(r'^prompt/(?P<pk>[0-9]+)/$', CreateResponseView.as_view(), name='create_response'),
        ]
    
    Or have a look at the code to get an idea of making your own view.

    For example, you can sub-class `CreateResponseView` and override `get_prompt()`
    to choose a different way of obtaining the prompt object.


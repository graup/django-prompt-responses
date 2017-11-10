from django.db import transaction
from django.views.generic import CreateView
from django.views.generic.detail import SingleObjectMixin
from .forms import ResponseForm, ResponseTagsForm
from .models import Prompt, Response
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core.urlresolvers import resolve
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured


class PromptInstanceMixin(object):
    """
    Provide prompt and prompt_instance to a view.

    Tries to get prompt by looking up pk parameter from url.
    Override get_prompt() to choose a different way of obtaining prompt.
    
    Implementation is similar to Django's SingleObjectMixin, but with different
    method names to not conflict with other generic views.
    """
    pk_url_kwarg = 'pk'
    prompt_model = Prompt
    prompt_queryset = None

    @cached_property
    def prompt(self):
        return self.get_prompt()

    @cached_property
    def prompt_instance(self):
        return self.prompt.get_instance()

    def get_prompt_queryset(self):
        if self.prompt_queryset is None:
            if self.prompt_model:
                return self.prompt_model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a QuerySet. Define "
                    "%(cls)s.prompt_model, %(cls)s.prompt_queryset, or override "
                    "%(cls)s.get_prompt_queryset()." % {
                        'cls': self.__class__.__name__
                    }
                )
        return self.prompt_queryset.all()

    def get_prompt(self):
        """Will throw propagate model.DoesNotExist if prompt does not exist"""
        queryset = self.get_prompt_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)
        else:
            raise AttributeError("Generic detail view %s must be called with "
                                 "either an object pk or a slug."
                                 % self.__class__.__name__)
        return queryset.get()

    def get_context_data(self, **kwargs):
        """Insert the single prompt object into the context dict."""
        context = {}
        if self.prompt:
            context['prompt'] = self.prompt
            context['prompt_instance'] = self.prompt_instance
        context.update(kwargs)
        return super(PromptInstanceMixin, self).get_context_data(**context)


class BaseCreateResponseView(PromptInstanceMixin, CreateView):
    form_class = ResponseForm
    template_name = 'prompt_responses/create_response.html'
    model = Response

    def get_user(self):
        raise ImproperlyConfigured(
            "It is necessary to override "
            "%(cls)s.get_user()." % {
                'cls': self.__class__.__name__
            }
        )

    def get_form_kwargs(self):
        kwargs = super(BaseCreateResponseView, self).get_form_kwargs()
        kwargs.update({'prompt_instance': self.prompt_instance})
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(BaseCreateResponseView, self).get_context_data(**kwargs)
        initial = []
        if self.prompt_instance.response_objects:
            initial = [{
                'content_type': ContentType.objects.get_for_model(obj),
                'object_id': obj.pk
            } for obj in self.prompt_instance.response_objects]
        if self.request.POST:
            data['formset'] = ResponseTagsForm(self.request.POST, instance=self.object, initial=initial)
        else:
            data['formset'] = ResponseTagsForm(instance=self.object, initial=initial)
        data['formset'].extra = len(initial)
        return data

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        form.instance.user = self.get_user()
        self.object = form.save()
        if formset.is_valid():
            formset.instance = self.object
            formset.save()

        return super(BaseCreateResponseView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'prompt_responses:create_response',
            args=[self.prompt.pk],
            current_app=self.request.resolver_match.namespace
        )


class CreateResponseView(LoginRequiredMixin, BaseCreateResponseView):
    def get_user(self):
        return self.request.user

from django import forms
from django.forms.models import inlineformset_factory
from .models import Prompt, Response, Tag
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured


class ResponseForm(forms.ModelForm):
    rating = forms.TypedChoiceField(choices=[], widget=forms.RadioSelect, coerce=int)

    def make_rating_choices(self, low, high):
        return [(i, str(i)) for i in range(low, high+1)]

    class Meta:
        model = Response
        fields = ('prompt', 'rating', 'text', 'content_type', 'object_id')
        widgets = {
            'prompt': forms.HiddenInput(),
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }
    
    def __init__(self, prompt_instance=None, *args, **kwargs):
        if not prompt_instance:
            raise ImproperlyConfigured(
                "%(cls)s needs to be instantiated with prompt_instance. "
                "Either call %(cls)s() with prompt_instance argument or "
                "use get_form_kwargs() in your FormView." % {
                    'cls': self.__class__.__name__
                }
            )

        super(ResponseForm, self).__init__(*args, **kwargs)

        # Update fields based on prompt type
        if prompt_instance.prompt.type == Prompt.TYPES.likert:
            del self.fields['text']
            self.fields['rating'].required = True
            if not prompt_instance.prompt.scale:
                scale = 5
            else:
                scale = prompt_instance.prompt.scale
            self.fields['rating'].choices = self.make_rating_choices(1, scale)
        if prompt_instance.prompt.type == Prompt.TYPES.openended:
            del self.fields['rating']
            self.fields['text'].required = True
        if prompt_instance.prompt.type == Prompt.TYPES.tagging:
            del self.fields['rating']
            del self.fields['text']
        
        # Set initial values based on prompt instance
        self.initial['prompt'] = prompt_instance.prompt
        self.initial['content_type'] = ContentType.objects.get_for_model(prompt_instance.object)
        self.initial['object_id'] = prompt_instance.object.pk


class TagForm(forms.ModelForm):
    @property
    def object(self):
        """
        Convert response_object into proper model for use in template.
        Example: `{% for form in formset %}{{form.object}}{% endfor %}`
        """
        if not self.initial.get('content_type'):
            return None
        if not self.initial.get('object_id'):
            return None
        return self.initial.get('content_type').get_object_for_this_type(
            pk=self.initial.get('object_id')
        )

    rating = forms.TypedChoiceField(
        choices=range(0,5), widget=forms.RadioSelect, coerce=int
    )

    class Meta:
        model = Tag
        fields = ('rating', 'content_type', 'object_id')
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }


ResponseTagsForm = inlineformset_factory(Response, Tag, form=TagForm, can_delete=False, extra=0)
from rest_framework import serializers
from .models import Prompt, PromptSet, Response, Tag
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from rest_framework.reverse import reverse


class PromptSetPromptInstanceHyperlink(serializers.HyperlinkedRelatedField):
    "URL for next prompt's instance based on current prompt"
    view_name = 'prompt-instantiate-from-set'

    def get_url(self, obj, view_name, request, format):
        if not obj.first_prompt:
            return None
        url_kwargs = {
            'promptset_name': obj.name,
            'pk': obj.first_prompt.pk
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class NextPromptInstanceHyperlink(serializers.HyperlinkedRelatedField):
    "URL for next prompt's instance based on current prompt"
    view_name = 'prompt-instantiate-from-set'

    def get_url(self, obj, view_name, request, format):
        if not obj.next_prompt:
            return None
        url_kwargs = {
            'promptset_name': obj.promptset.name,
            'pk': obj.next_prompt.pk
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class PromptSetSerializer(serializers.HyperlinkedModelSerializer):
    next_prompt_instance = PromptSetPromptInstanceHyperlink(source="*", read_only=True)
    ordered_prompts = serializers.HyperlinkedIdentityField(
        view_name='prompt-detail', source="prompts", many=True, read_only=True
    )

    class Meta:
        model = PromptSet
        fields = ('url', 'ordered_prompts', 'next_prompt_instance', )
        lookup_field = 'name'
        extra_kwargs = {
            'url': {'lookup_field': 'name'}
        }

class PromptSerializer(serializers.HyperlinkedModelSerializer):
    instance_url = serializers.HyperlinkedIdentityField(view_name='prompt-instantiate')
    prompt_object_type = serializers.CharField()
    response_object_type = serializers.CharField()

    class Meta:
        model = Prompt
        fields = (
            'url',
            'instance_url',
            'type',
            'scale_min', 'scale_max', 'text',
            'prompt_object_type', 'response_object_type',
        )

class GenericSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    __str__ = serializers.CharField()
    object_type = serializers.SerializerMethodField()

    def get_object_type(self, obj):
        return str(ContentType.objects.get_for_model(obj))

    class Meta:
        fields = ('id', '__str__', )

class PromptInstanceSerializer(serializers.Serializer):
    next_prompt_instance = NextPromptInstanceHyperlink(source="*", read_only=True)
    response_create_url = serializers.HyperlinkedRelatedField(
        view_name='prompt-create-response', source='prompt', read_only=True
    )
    promptset = serializers.HyperlinkedRelatedField(
        view_name='promptset-detail', lookup_field='name', read_only=True
    )
    prompt = PromptSerializer()
    object = GenericSerializer()
    response_objects = GenericSerializer(many=True)
    display_text = serializers.CharField(source="__str__")
    
    class Meta:
        fields = ('url', 'next_prompt_instance', 'response_url', 'display_text', 'prompt', 'object', 'response_objects', )

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('rating', 'object_id',)

class ResponseSerializer(serializers.ModelSerializer):
    prompt = serializers.PrimaryKeyRelatedField(queryset=Prompt.objects)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Response
        fields = ('prompt', 'rating', 'text', 'object_id', 'tags', )

    def create(self, validated_data):
        prompt = validated_data.pop('prompt')
        user = self.context['request'].user if self.context['request'].user.is_authenticated() else None
        try:
            return prompt.create_response(user=user, **validated_data)
        except ValidationError as e:
            # Propagate Django's validation errors
            try:
                errors = e.message_dict
            except AttributeError:
                errors = {'errors': e}
            raise serializers.ValidationError(errors)


from rest_framework import serializers
from .models import Prompt, Response, Tag
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

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
    response_create_url = serializers.HyperlinkedRelatedField(view_name='prompt-create-response', source='prompt', read_only=True)
    prompt = PromptSerializer()
    object = GenericSerializer()
    response_objects = GenericSerializer(many=True)
    display_text = serializers.CharField(source="__str__")

    class Meta:
        fields = ('url', 'response_url', 'display_text', 'prompt', 'object', 'response_objects', )

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


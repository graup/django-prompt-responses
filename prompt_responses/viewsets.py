from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    PromptSerializer, PromptSetSerializer, PromptInstanceSerializer, ResponseSerializer
)
from .models import Prompt, PromptSet


class PromptSetViewSet(viewsets.ReadOnlyModelViewSet):
    "API for Prompt sets. Read-only"
    queryset = PromptSet.objects.all()
    serializer_class = PromptSetSerializer
    permission_classes = []
    lookup_field = 'name'


class PromptViewSet(viewsets.ReadOnlyModelViewSet):
    "API for Prompts. Read-only except create-response"
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    permission_classes = []

    def _instantiate(self, request, pk=None, promptset=None):
        prompt = self.get_object()
        instance = prompt.get_instance(promptset=promptset)
        context = {'request': request}
        instance_serializer = PromptInstanceSerializer(instance, context=context)
        return Response(instance_serializer.data)

    @detail_route(methods=['get'], url_name='instantiate')
    def instantiate(self, request, pk=None):
        """Get a new instance for a prompt"""
        return self._instantiate(request, pk)

    @detail_route(methods=['get'], url_name='instantiate-from-set', url_path='instantiate/(?P<promptset_name>[\w-]+)')
    def instantiate_from_set(self, request, pk=None, promptset_name=None):
        """Get a new instance for a prompt, within a promptset"""
        promptset = PromptSet.objects.get(name=promptset_name)
        return self._instantiate(request, pk, promptset)

    @detail_route(methods=['post'], url_path='create-response', permission_classes=[])
    def create_response(self, request, pk=None):
        """Create a response for a prompt. Request needs to be authenticated"""
        # This call needs to be authenticated as every request is assigned to a user
        if not self.request.user or not self.request.user.is_authenticated():
            raise NotAuthenticated()

        data = {}
        data.update(**request.data)
        data['prompt'] = self.get_object().pk
        context = {'request': request}
        serializer = ResponseSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

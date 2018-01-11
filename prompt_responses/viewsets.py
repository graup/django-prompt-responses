from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, NotFound
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    PromptSerializer, PromptSetSerializer, PromptInstanceSerializer, ResponseSerializer
)
from .models import Prompt, PromptSet
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _


class PromptSetViewSet(viewsets.ReadOnlyModelViewSet):
    "API for Prompt sets. Read-only"
    queryset = PromptSet.objects.all()
    serializer_class = PromptSetSerializer
    permission_classes = []
    lookup_field = 'name'

    @detail_route(methods=['get'], url_name='statistics')
    def statistics(self, request, name=None):
        """
        Get statistics for each prompt in this promptset.
        See PromptSet.get_prompt_statistics for details.
        """
        promptset = self.get_object()
        context = {'request': request}
        series = []
        # get overall stats
        series.append({
            'name': 'all',
            'label': _('all'),
            'prompt_data': promptset.get_prompt_statistics(
                subset=None,
                object_ids=request.query_params.get('object_ids', None),
                response_object_ids=request.query_params.get('response_object_ids', None)
            ),
        })
        # get stats for one user
        if self.request.user.is_authenticated:
            series.append({
                'name': 'current_user',
                'label': _('me'),
                'prompt_data': promptset.get_prompt_statistics(
                    subset=None,
                    user_id=self.request.user.id,
                    object_ids=request.query_params.get('object_ids', None),
                    response_object_ids=request.query_params.get('response_object_ids', None)
                ),
            })
        data = {
            'ordered_prompts': PromptSerializer(promptset.prompts.all(), many=True, context=context).data,
            'series': series
        }
        return Response(data)


class PromptViewSet(viewsets.ReadOnlyModelViewSet):
    "API for Prompts. Read-only except create-response"
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    permission_classes = []

    def _instantiate(self, request, pk=None, promptset=None):
        prompt = self.get_object()
        try:
            instance = prompt.get_instance(
                promptset=promptset,
                object_id=request.query_params.get('object_id', None),
                response_object_ids=request.query_params.get('response_object_ids', None)
            )
        except ObjectDoesNotExist:
            raise NotFound(_('The prompt object could not be found.'))
    
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
        # This request needs to be authenticated as every response is assigned to a user
        if not self.request.user or not self.request.user.is_authenticated:
            raise NotAuthenticated()

        data = {}
        data.update(**request.data)
        data['prompt'] = self.get_object().pk
        context = {'request': request}
        serializer = ResponseSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

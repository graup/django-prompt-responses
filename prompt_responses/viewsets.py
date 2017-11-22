from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated
from .serializers import PromptSerializer, PromptInstanceSerializer, ResponseSerializer
from .models import Prompt
from django.views.decorators.csrf import csrf_exempt


class PromptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer

    @detail_route(methods=['get'],)
    def instantiate(self, request, pk=None):
        """Get a new instance for a prompt"""
        prompt = self.get_object()
        instance = prompt.get_instance()
        context = {'request': request}
        instance_serializer = PromptInstanceSerializer(instance, context=context)
        return Response(instance_serializer.data)

    @csrf_exempt
    @detail_route(methods=['post'], url_path='create-response')
    def create_response(self, request, pk=None):
        """Create a response for a prompt"""
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

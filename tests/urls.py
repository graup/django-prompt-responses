from django.conf.urls import url, include
from rest_framework import routers
from prompt_responses.viewsets import *

router = routers.DefaultRouter()
router.register(r'prompts', PromptViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'', include('prompt_responses.urls', namespace='prompt_responses')),
]


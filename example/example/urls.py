from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from prompt_responses.viewsets import *

router = routers.DefaultRouter()
router.register(r'prompts', PromptViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'', include('prompt_responses.urls', namespace='prompt_responses')),
]


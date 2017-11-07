# -*- coding: utf-8 -*-
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    ListView
)

from .models import (
	Prompt,
	PromptVersion,
	Response,
	Tag,
)


class PromptCreateView(CreateView):

    model = Prompt


class PromptDeleteView(DeleteView):

    model = Prompt


class PromptDetailView(DetailView):

    model = Prompt


class PromptUpdateView(UpdateView):

    model = Prompt


class PromptListView(ListView):

    model = Prompt


class PromptVersionCreateView(CreateView):

    model = PromptVersion


class PromptVersionDeleteView(DeleteView):

    model = PromptVersion


class PromptVersionDetailView(DetailView):

    model = PromptVersion


class PromptVersionUpdateView(UpdateView):

    model = PromptVersion


class PromptVersionListView(ListView):

    model = PromptVersion


class ResponseCreateView(CreateView):

    model = Response


class ResponseDeleteView(DeleteView):

    model = Response


class ResponseDetailView(DetailView):

    model = Response


class ResponseUpdateView(UpdateView):

    model = Response


class ResponseListView(ListView):

    model = Response


class TagCreateView(CreateView):

    model = Tag


class TagDeleteView(DeleteView):

    model = Tag


class TagDetailView(DetailView):

    model = Tag


class TagUpdateView(UpdateView):

    model = Tag


class TagListView(ListView):

    model = Tag


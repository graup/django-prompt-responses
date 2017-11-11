from django.contrib import admin

from . import models


class PromptSetAdmin(admin.ModelAdmin):
    list_display = ("name", "created")
admin.site.register(models.PromptSet, PromptSetAdmin)


class PromptAdmin(admin.ModelAdmin):
    list_display = ("type", "text", "created", 'prompt_object_type', 'response_object_type')
    list_filter = ("type", 'prompt_object_type', 'response_object_type')
admin.site.register(models.Prompt, PromptAdmin)


class TagInline(admin.TabularInline):
    model = models.Tag


class ResponseAdmin(admin.ModelAdmin):
    list_display = ("created", "rating", "text", "prompt_object")
    raw_id_fields = ("user", )
    inlines = [
        TagInline,
    ]
admin.site.register(models.Response, ResponseAdmin)


class TagAdmin(admin.ModelAdmin):
    list_display = ("rating", "response_object",)
admin.site.register(models.Tag, TagAdmin)


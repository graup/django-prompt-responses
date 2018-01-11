from django.contrib import admin

from . import models

from functools import partial


def model_link(instance):
    if not instance:
        return None
    label = str(instance)
    truncated_label = label[:25]
    if len(label) > 25:
        truncated_label += '...'
    return '<a href="../../%s/%s/%d">%s</a>' % (
        instance._meta.app_label,
        instance._meta.model_name,
        instance.pk,
        truncated_label
    )

def foreign_key_link(instance, field):
    return model_link(getattr(instance, field))
    
class ForeignKeyLinks(object):
    "Source: https://stackoverflow.com/a/3157065/700283"
    def __getattr__(cls, name):
        if name[:8] == 'link_to_':
            method = partial(foreign_key_link, field=name[8:])
            method.__name__ = name[8:]
            method.allow_tags = True
            setattr(cls, name, method)
            return getattr(cls, name)
        raise AttributeError


class PromptSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
admin.site.register(models.PromptSet, PromptSetAdmin)


class PromptAdmin(admin.ModelAdmin):
    list_display = ('text', 'type', 'prompt_object_type', 'response_object_type', 'created')
    list_filter = ('type', 'prompt_object_type', 'response_object_type')
admin.site.register(models.Prompt, PromptAdmin)


class TagInline(admin.TabularInline):
    model = models.Tag


class ResponseAdmin(ForeignKeyLinks, admin.ModelAdmin):
    list_display = ('created', 'link_to_prompt', 'link_to_user', 'link_to_prompt_object', 'rating', 'text', 'response_objects')
    raw_id_fields = ('user', )
    inlines = [TagInline]

    def get_queryset(self, request):
        return super(ResponseAdmin,self).get_queryset(request).prefetch_related('tags')

    def response_objects(self, instance):
        if instance.tags.count():
            def tag_label(tag):
                return '%s (%d)' % (model_link(tag.response_object), tag.rating)
            return ', '.join(map(tag_label, instance.tags.all()))
        return None
    response_objects.allow_tags = True

admin.site.register(models.Response, ResponseAdmin)


class TagAdmin(admin.ModelAdmin):
    list_display = ("rating", "response_object")
admin.site.register(models.Tag, TagAdmin)


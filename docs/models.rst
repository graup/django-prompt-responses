=====
Models
=====

This page gives a discription of the implemented models and their relations.

Prompt
======

.. class:: Prompt

    A Prompt is an abstract definition of a task or question that will be presented to a user
    in order to collect responses.

    In order to present a Prompt to a user, it needs to be instantiated by calling :func:`get_instance() <Prompt.get_instance>`.

    In its simplest form, a Prompt defines some `text` and a `type` for either free-form
    or rating responses.

    A more advanced version can be connected to any other type of object. When instantiated,
    these Prompts will be populated with one object chosen from the set of objects of the defined type.
    The default implementation returns one random object, but this can be customized.

    The most advanced version defines two types of objects and allows for tagging, i.e. the user
    is asked to rate the relationship between objects of the first set and objects of the second.
    When instantiated, these Prompts will be populated with one object chosen of the first type
    and a number of objects of the second type.

    Prompts also offer a range of analysis functions. For the sake of readability, these are documented :doc:`here <analysis>`.

    .. attribute:: type

        The type of the Prompt. Currently supported types: likert, openended, tagging

    .. attribute:: text

        The text to be displayed to the user. The string can use the `{object}` placeholder
        which will be replaced by the object the prompt is instantiated with.
    
    .. attribute:: scale_min

        For prompts with rating responses, the minimum value of the scale. Defaults to 1
    
    .. attribute:: scale_max
    
        For prompts with rating responses, the maximum value of the scale.

    .. attribute:: prompt_object_type
    
        An object of class `ContentType <https://docs.djangoproject.com/en/1.11/ref/contrib/contenttypes/>`_ to define the model of objects this prompt will be populated with when instantiated.
        One prompt instance will be populated with one object of this type.
        A response will contain a reference to this object.

    .. attribute:: response_object_type
    
        An object of class `ContentType <https://docs.djangoproject.com/en/1.11/ref/contrib/contenttypes/>`_  to define the model of objects this prompt will be populated with when instantiated.
        One prompt instance will be populated with a number of objects of this type.
        A response will create :class:`Tags <Tag>` with references to these objects.

    .. method:: get_instance()

        Instantiate this Prompt. Will get one or more objects, depending on the type of prompt.

        :return: :class:`PromptInstance`

    .. method:: create_response()

        Convenience function to create (and save) a :class:`Response` for this prompt.

        Pass :attr:`rating <Response.rating>` or :attr:`text <Response.text>`,
        as well as :attr:`user <Response.user>` and :attr:`prompt_object <Response.prompt_object>` as needed.

        To save tagging responses, pass `tags=[(object1, rating1), (object2, rating2), ...]`
        OR alternatively, `tags=[{'object_id': id1, 'rating': rating2}, ...]`

        Note that responses per se are not unique per user
        (as some experiments might require asking the same question multiple times).
        Some of the analytics functions offer a `user_unique` parameter to restrict analysis
        to the user's latest response only.

        In contrast, tags are ensured to be unique for (prompt, user, prompt_object, response_object).
        If the user tagged this combination before, the Tag will be updated, incl. its response relation 
        (i.e. the original Response object will no longer be associated with this tag).

        This method verifies that the objects match the models defined in the :class:`Prompt` and
        raises a `ValidationException` on a mismatch.

        :returns: the newly created :class:`Response`
    
    .. method:: get_object()

        Used to determine the object for instantiating this prompt.
        The default implementation is to retrieve a random object from the queryset.
        You can override this method to customize this behavior.
        See :attr:`Prompt.prompt_object_type`.

    .. method:: get_queryset()

        The queryset from which the object will be drawn when instantiating this Prompt.
        The default implementation is to return all objects of type :attr:`Prompt.prompt_object_type`.

    .. method:: get_response_objects()

        Used to determine the objects for instantiating this prompt.
        The default implementation is to retrieve a number of random objects from the queryset.
        You can override this method to customize this behavior.
        See :attr:`Prompt.response_object_type`.

    .. method:: get_response_queryset()

        The queryset from which the objects will be drawn when instantiating this prompt.
        The default implementation is to return all objects of type :attr:`Prompt.response_object_type`.

Scales
------

For prompts that require rating responses, usually you want to confine the acceptable values to a certain scale.

The `Prompt` model offers some utility functions to create arbitrary scales for displaying them in forms.

TODO

PromptInstance
--------------

.. class:: PromptInstance

    A PromptInstance is not a database model, but created on the fly when a prompt is instantiated.
    It encapsulates the prompt and any object instances that are needed to display it to the user.
    It only lives for one request.

    .. attribute:: prompt

        :type: :class:`Prompt`

    .. attribute:: object

        An object with which this prompt has been populated.
        See :attr:`Prompt.prompt_object_type`.

    .. attribute:: response_objects

        A list of objects with which this prompt has been populated. Can be presented for tagging prompts.
        See :attr:`Prompt.response_object_type`.
    
    .. method:: __str__

        The string representation of this class is the prompt's text, formatted with the `object`.
        Useful for directly printing a `prompt_instance` in a template.
        See :attr:`Prompt.text`.

Response
========

.. class:: Response

    A Response can have a rating and/or a text.
    If the prompt has a :attr:`prompt_object_type <Prompt.prompt_object_type>`,
    the object obtained during instantiation should be saved as prompt_object.

    .. attribute:: rating

        :type: integer

    .. attribute:: text

        Textual response. This is a TEXT field in the database, so it can contain arbitrary length of texts.
        If you need to save additional data, you can use this field to save JSON encoded data.

        :type: string

    .. attribute:: prompt_object

        Any object that this response is related to.
        Its type should match :attr:`prompt_object_type <Prompt.prompt_object_type>`.

    .. attribute:: prompt

        The :class:`Prompt` that this response is related to. This is a required field.

    .. attribute:: user

        The user that this response belongs to. This is a required field.

Tag
===

.. class:: Tag

    User ratings for associations between two objects.
    Tags are contained in a :class:`Response`. You shouldn't need to create these objects
    yourself – rather, refer to :func:`Prompt.create_response()`.

    .. attribute:: response

        The :class:`Response` that this tag is related to. This is a required field.

    .. attribute:: response_object

        The object that this tag refers to. Should match the type
        defined in the :class:`Prompt`.
        When you instantiate a Prompt, this should be one of the instance's
        :attr:`response_objects <PromptInstance.response_objects>`.
        See :attr:`Prompt.response_object_type`.

    .. attribute:: rating

        :type: integer

PromptSet
=========

.. class:: PromptInstance

    You can optionally use PromptSets to organize several prompts together.
    PromptSets have a `name` and contain an ordered list of :class:`Prompt` objects.

    .. attribute:: name

        A name to identify this set. Should be in slug format (alphanumerical and dashes).

    .. attribute:: prompts

        A many-to-many field to add any number of :class:`Prompts <Prompt>` to this set.
        Prompts are orderable.
        See `django-sortedm2m's documentation <https://github.com/gregmuellegger/django-sortedm2m>`_ for details
        about how this works. If added `sortedm2m` to your `INSTALLED_APPS`,
        the Django admin widget should allow drag and drop.

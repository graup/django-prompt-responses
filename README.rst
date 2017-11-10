=============================
prompt_responses
=============================

.. image:: https://badge.fury.io/py/django-prompt-responses.svg
    :target: https://badge.fury.io/py/django-prompt-responses

.. image:: https://travis-ci.org/graup/django-prompt-responses.svg?branch=master
    :target: https://travis-ci.org/graup/django-prompt-responses

.. image:: https://codecov.io/gh/graup/django-prompt-responses/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/graup/django-prompt-responses

A flexible prompt and user responses data schema utilizing Django's content types framework.

This app was born during a university research project. The main use case is data collection.
It lets you create numerous kinds of "prompts" (questions or tasks) and record user responses.
Prompts can be populated with any kind of database object.

This supports these kind of prompts:

* How do you feel today on a 1-5 scale? (Simple likert question)
* How do you like {object} on a 1-10 scale? (Object-based likert question)
* Which word do you associate with {object}? (Object-based open-ended question)
* How related do you think is {object} to these other objects? (Tagging task)

Ratings and tags are simply integer values, their meaning can be defined by your application
(e.g. 1 to 5 scales, or -1 = no, +1 = yes, and so on).

Documentation
-------------

The full documentation is at https://django-prompt-responses.readthedocs.io.

Quickstart
----------

Install prompt_responses::

    pip install django-prompt-responses

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'prompt_responses.apps.PromptResponsesConfig',
        ...
    )

Create Prompts, e.g. through the integrated admin views.

Deliver a prompt to the user:

.. code-block:: python

    prompt = Prompt.objects.get(id=1)
    instance = prompt.get_instance()
    
    """
    Use these variables to display the UI:
    prompt.type
    str(instance)
    instance.object
    instance.response_objects
    """

Save a user response:

.. code-block:: python

    prompt = Prompt.objects.get(id=1)
    prompt.create_response(
        user=user,
        prompt_object=instance.object,
        rating=5
    )

Analyze data:

.. code-block:: python

    prompt = Prompt.objects.get(id=1)
    # Mean rating for all responses
    rating = prompt.get_mean_rating()
    # Mean ratings for all objects
    matrix = prompt.get_mean_tag_rating_matrix()
    # Mean ratings for one object
    ratings = list(prompt.get_mean_tag_ratings(instance.object))

Features
--------

* Prompt types

  * Likert scale ratings
  * Open-ended free text
  * Tagging

* Populate prompts with objects in order to

  * let users rate objects from one set
  * let users rate (tag) relations between two sets of objects

* Analytics convenience functions
* (Coming soon) Plugable object sampling algorithms

Running Tests

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage

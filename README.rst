=============================
prompt_responses
=============================

.. image:: https://badge.fury.io/py/django-prompt-responses.svg
    :target: https://badge.fury.io/py/django-prompt-responses

.. image:: https://travis-ci.org/graup/django-prompt-responses.svg?branch=master
    :target: https://travis-ci.org/graup/django-prompt-responses

.. image:: https://codecov.io/gh/graup/django-prompt-responses/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/graup/django-prompt-responses

A flexible prompt and user responses data schema utilizing the generic content types.

This app was born during a research project. The main use case is data collection.
It lets you create numerous kinds of "prompts" (e.g. questions or tasks) and record user responses.

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

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage

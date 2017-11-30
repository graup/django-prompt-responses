============
Installation
============

Install with pip

.. sourcecode:: sh

    $ pip install django-prompt-responses

Add it to your `INSTALLED_APPS`

.. code-block:: python

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        ...
        'prompt_responses',
        'sortedm2m',  # for the ability to change the order of Prompts in the Django admin
        ...
    )

Sync your database

.. sourcecode:: sh

    $ python manage.py migrate prompt_responses

Head to the :doc:`usage <usage>` section for the next steps.
# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import django

# The test runner sets DEBUG=False anyway. You can reanble it per testcase if needed.
DEBUG = False
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "b^f7e36+1(lqzv$1yew2zno2n!d7yefv%tw+pj_9yf@9o9xm-x"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "prompt_responses",
    "tests"
]

LOGGING = {
    'version': 1,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    },
}

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = ()
else:
    MIDDLEWARE_CLASSES = ()

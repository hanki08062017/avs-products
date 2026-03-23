from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-wuyjeal4)br&9c^k0r6m4ju+n_op$1gzts9vx9fq985lg+or7e')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [h for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'customer',
    'seller',
    'management',
    'mathfilters',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Ecom_System.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'seller.context_processors.staff_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'Ecom_System.wsgi.application'

# ── Database & Storage — loaded from db_config.py (reads .env) ───────────────
from Ecom_System.db_config import DATABASES, STORAGES, MEDIA_URL  # noqa
from Ecom_System.db_config import (                                 # noqa
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME,
    AWS_S3_ENDPOINT_URL, AWS_S3_REGION_NAME, AWS_DEFAULT_ACL,
    AWS_QUERYSTRING_AUTH, AWS_S3_FILE_OVERWRITE, AWS_S3_CUSTOM_DOMAIN,
)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

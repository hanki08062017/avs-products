"""
db_config.py — Database & Storage configuration
Reads from .env file. Works across development, testing and production.
To switch environments, change DJANGO_ENV in .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.environ.get('DJANGO_ENV', 'development')  # development | testing | production

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ['DB_NAME'],
        'USER':     os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST':     os.environ['DB_HOST'],
        'PORT':     os.environ.get('DB_PORT', '5432'),
        'OPTIONS':  {'sslmode': 'require'},
    }
}

# ── Supabase Storage ──────────────────────────────────────────────────────────
_project_url = os.environ['SUPABASE_PROJECT_URL']
_bucket      = os.environ.get('SUPABASE_BUCKET', 'media')

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

AWS_ACCESS_KEY_ID       = os.environ['S3_ACCESS_KEY']
AWS_SECRET_ACCESS_KEY   = os.environ['S3_SECRET_KEY']
AWS_STORAGE_BUCKET_NAME = _bucket
AWS_S3_ENDPOINT_URL     = os.environ['S3_ENDPOINT']
AWS_S3_REGION_NAME      = os.environ.get('S3_REGION', 'ap-northeast-1')
AWS_DEFAULT_ACL         = 'public-read'
AWS_QUERYSTRING_AUTH    = False
AWS_S3_FILE_OVERWRITE   = False
AWS_S3_CUSTOM_DOMAIN    = f"{_project_url.replace('https://', '')}/storage/v1/object/public/{_bucket}"

MEDIA_URL = f'{_project_url}/storage/v1/object/public/{_bucket}/'

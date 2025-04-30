from .base import *
from dotenv import load_dotenv

load_dotenv()

ALLOWED_HOSTS = ["*"]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DATABASE_PASSWORD"),
        'HOST': os.getenv("HOST"),
        'PORT': os.getenv("PORT"),

    }
}

# email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_SSL = True
EMAIL_USE_TSL = False
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = os.getenv("EMAIL")
EMAIL_HOST_PASSWORD = os.getenv("PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("EMAIL")

# celery for prod (docker)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

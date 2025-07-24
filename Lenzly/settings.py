# project/settings.py
import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-q1l&d6kx(9p-^8dga3i855ewfp8nz0co3b@(jacjfo+#xmkmo#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party libraries
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'phonenumber_field',
    'channels',

    # Local apps
    'auth_system',
    'profiles_system.apps.ProfileSystemConfig',
    'follow_system.apps.FollowSystemConfig',
    'post_app.apps.PostAppConfig',
    'story_app.apps.StoryAppConfig',
    'chat_system.apps.ChatSystemConfig'
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# CORS_ALLOW_ALL_ORIGINS = True  # development üçün

ROOT_URLCONF = 'Lenzly.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Lenzly.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ADDITIONS
AUTH_USER_MODEL = 'auth_system.User'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Email settings (example using SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'kemalegunesli39@gmail.com'
EMAIL_HOST_PASSWORD = 'swjo loyp drdb zigq'

# Celery settings
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'   # və ya os.path.join(BASE_DIR, 'media')

# 3. URLs-də media fayllara xidmət etmək üçün
#    project/urls.py-da aşağıdakını import və urlpatterns-ə əlavə edin:
#
# from django.conf import settings
# from django.conf.urls.static import static
#
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 4. Celery ayarları — artıq broker və backend təyin etmisiniz, indi beat schedule əlavə edin
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Hər 5 dəqiqədən bir expired story-ləri yoxlayıb arxivləmək üçün (əlavə təhlükəsizlik)
    'cleanup_expired_stories': {
        'task': 'story_app.tasks.archive_story_batch',
        'schedule': crontab(minute='*/5'),
    },
}

# 5. story_app/tasks.py içində batch arxiv tapşırığı
#    @shared_task
#    def archive_story_batch():
#        now = timezone.now()
#        expired = Story.objects.filter(is_archived=False, expires_at__lte=now)
#        expired.update(is_archived=True)

# 6. REST Framework üçün pagination və ya əlavə permission tələb edirsinizsə
REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'] = 'rest_framework.pagination.PageNumberPagination'
REST_FRAMEWORK['PAGE_SIZE'] = 20

# 7. (İstəyə bağlı) CORS / CSRF tənzimləmələri
# CORS_ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.com",
    # əlavə origin-lər...
# ]
# və ya dev üçün:
# CORS_ALLOW_ALL_ORIGINS = True

ASGI_APPLICATION = 'Lenzly.asgi.application'


# Channel layer konfiqurasiyası:
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
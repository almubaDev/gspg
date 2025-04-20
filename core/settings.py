from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent



SECRET_KEY = 'django-insecure-qi4sghp-7m)e#zc%fh0i1y=p2p7o#!6qma18i!iy-vr0_3mm=6'

DEBUG = True

ALLOWED_HOSTS = []



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps locales
    'users',
    'gspg',
    'gspg_client',
    #'whatsapp_bot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'gspg_client.middleware.UniversidadConfigMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'gspg.context_processors.user_magister_context',

            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True



STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Usuario personalizado
AUTH_USER_MODEL = 'users.CustomUser'

# Configuración de autenticación
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# URLs para redirect después de login/logout
LOGIN_REDIRECT_URL = 'gspg:dashboard'
LOGOUT_REDIRECT_URL = 'users:login'
LOGIN_URL = 'users:login'


# WHATSAPP_API_TOKEN = "EAASQFZC6QEZBABO7Jwg6zgZAEOkINHlGUTZAALc5iZCX2S031Kq1dGKK9hq9m1lqhbYtt9JZBNbmbx9X8S5hHcUZC5bPcH4JKC9EoZAt3dSW0V0OlpJbPVhNDVedTE34ChlXqB9QxusRK2MqgRqWNl0PZBtWpfAYb5hrgQZA2V8aZAbQcoRlR3B7TmoI6SqzzdwnWiMWBV3eY41ZCnZAd9lZBQc7jsp2R6"
# WHATSAPP_PHONE_ID = "557369467459256"
# WHATSAPP_VERIFY_TOKEN = "Anada!312$"
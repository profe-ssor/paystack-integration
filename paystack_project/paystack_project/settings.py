from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
# This will automatically load .env file if it exists

# --- ENVIRONMENT DETECTION ---
def is_production():
    """Detect if running in production environment"""
    # Check for common production indicators
    production_indicators = [
        os.environ.get('RENDER', False),  # Render hosting
        os.environ.get('HEROKU', False),  # Heroku hosting
        os.environ.get('RAILWAY', False),  # Railway hosting
        os.environ.get('VERCEL', False),  # Vercel hosting
        os.environ.get('DATABASE_URL', '').startswith('postgres'),  # PostgreSQL URL
        os.environ.get('DYNO', False),  # Heroku dyno
        os.environ.get('PORT', False),  # Production port
    ]
    return any(production_indicators)

# --- SECURITY SETTINGS ---
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-key-for-development')

# Explicit DEBUG setting - check environment first, then fall back to production detection
debug_env = config('DEBUG', default=None)
if debug_env is not None:
    DEBUG = str(debug_env).lower() in ('true', '1', 'yes', 'on')
else:
    DEBUG = not is_production()  # Auto-detect if DEBUG not explicitly set

# Dynamic ALLOWED_HOSTS based on environment
if is_production():
    allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', 'paystack-integration-ldwp.onrender.com')
else:
    allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')

ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]

# --- APPLICATIONS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    # Local
    'payments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'paystack_project.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'paystack_project.wsgi.application'

# --- DATABASE CONFIGURATION ---

        # Development: Use SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASES["default"] = dj_database_url.parse("postgresql://paystackdb_user:mxEEe25NRYKRiDoaDKqRiYHff9ci2UwS@dpg-d1ir933ipnbc7380ctfg-a.oregon-postgres.render.com/paystackdb")

# --- PASSWORD VALIDATORS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Static files configuration for production
if is_production():
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    # Only add STATICFILES_DIRS if the directory exists
    static_dir = BASE_DIR / 'static'
    if static_dir.exists():
        STATICFILES_DIRS = [static_dir]

# --- DEFAULT PRIMARY KEY ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- REST FRAMEWORK ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# --- JWT SETTINGS ---
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,  # Changed to False to avoid blacklist issues
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=24),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# --- CORS HEADERS ---
CORS_ALLOW_CREDENTIALS = True

if is_production():
    # Production: Allow all origins for now (you can make this stricter later)
    CORS_ALLOW_ALL_ORIGINS = True
    # Fallback to specific origins if needed
    cors_origins_env = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://pay-stack-dun.vercel.app')
    CORS_ALLOWED_ORIGINS = [origin.strip().rstrip('/') for origin in cors_origins_env.split(',') if origin.strip()]
else:
    # Development: Relaxed CORS
    CORS_ALLOW_ALL_ORIGINS = True

# Additional CORS settings for better compatibility
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://pay-stack-dun.vercel.app",
    "https://paystack-integration-ldwp.onrender.com",
    "https://your-ecommerce-domain.com",  # Replace with your actual domain
]

# Allow all headers and methods
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_ALL_METHODS = True

# --- PAYSTACK KEYS ---
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default=None)
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default=None)
PAYSTACK_WEBHOOK_SECRET = config('PAYSTACK_WEBHOOK_SECRET', default='')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# --- LOGGING ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'paystack_api.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'payments': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
    },
    },
}

# --- PRODUCTION SECURITY SETTINGS ---
if is_production() and not DEBUG:
    # Production: Strict security (only when DEBUG is False)
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

    # Production: JSON only API
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
        'rest_framework.renderers.JSONRenderer',
    ]

    # Production: Error-level logging only
    LOGGING['handlers']['console']['level'] = 'ERROR'
    LOGGING['loggers']['django'] = {
        'handlers': ['console'],
        'level': 'ERROR',
        'propagate': True,
    }
else:
    # Development: Relaxed security for local development
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    
    # Development: Include browsable API
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]

# --- DEVELOPMENT DEBUG INFO ---
if DEBUG:
    print("=" * 50)
    print("DJANGO SETTINGS DEBUG INFO")
    print("=" * 50)
    print(f"DEBUG: {DEBUG}")
    print(f"Is Production: {is_production()}")
    print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    print(f"CORS_ALLOW_ALL_ORIGINS: {CORS_ALLOW_ALL_ORIGINS}")
    print(f"SECURE_SSL_REDIRECT: {globals().get('SECURE_SSL_REDIRECT', 'Not set')}")
    print(f"DATABASE: {'PostgreSQL' if is_production() else 'SQLite'}")
    print(f"PAYSTACK_PUBLIC_KEY: {PAYSTACK_PUBLIC_KEY[:20]}..." if PAYSTACK_PUBLIC_KEY else "Not set")
    print(f"FRONTEND_URL: {FRONTEND_URL}")
    print("=" * 50)
    print("🚀 Server starting in DEVELOPMENT mode")
    print("🔓 HTTPS enforcement is DISABLED")
    print("🌐 Access at: http://localhost:8000 or http://127.0.0.1:8000")
    print("❌ Do NOT use https://localhost:8000")
    print("=" * 50)

# --- CACHE CONFIGURATION ---
if is_production():
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# --- EMAIL CONFIGURATION ---
if is_production():
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- RENDER SPECIFIC SETTINGS ---
if os.environ.get('RENDER'):
    # Force HTTPS in production
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_TZ = True
    
    # Render-specific logging
    LOGGING['handlers']['console']['class'] = 'logging.StreamHandler'
    LOGGING['handlers']['console']['stream'] = 'ext://sys.stdout'
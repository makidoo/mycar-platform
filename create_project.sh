# ========================================
# FICHIER 1: docker-compose.local.yml
# ========================================
cat <<'EOF' > docker-compose.local.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mycar_local
      POSTGRES_USER: mycar_user
      POSTGRES_PASSWORD: localpass123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_local:/var/lib/postgresql/data
    networks:
      - mycar_local_network

  web:
    build:
      context: .
      dockerfile: Dockerfile.local
    command: python manage.py runserver 0.0.0.0:8000
    environment:
      - DEBUG=True
      - DB_HOST=db
      - DB_NAME=mycar_local
      - DB_USER=mycar_user
      - DB_PASSWORD=localpass123
      - SECRET_KEY=django-insecure-local-dev-key-only-change-me
      - ALLOWED_HOSTS=localhost,127.0.0.1
      - MOCK_SERVICES=True
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    networks:
      - mycar_local_network

volumes:
  postgres_data_local:

networks:
  mycar_local_network:
    driver: bridge
EOF

# ========================================
# FICHIER 2: Dockerfile.local
# ========================================
cat <<'EOF' > Dockerfile.local
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
EOF

# ========================================
# FICHIER 3: .env
# ========================================
cat <<'EOF' > .env
DEBUG=True
SECRET_KEY=django-insecure-local-dev-key-only-change-me
DB_HOST=localhost
DB_NAME=mycar_local
DB_USER=mycar_user
DB_PASSWORD=localpass123
ALLOWED_HOSTS=localhost,127.0.0.1
MOCK_SERVICES=True
EOF

# ========================================
# FICHIER 4: requirements.txt
# ========================================
cat <<'EOF' > requirements.txt
Django==5.0.2
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1
qrcode[pil]==7.4.2
psycopg2-binary==2.9.9
python-decouple==3.8
Pillow==10.2.0
django-cors-headers==4.3.1
reportlab==4.0.9
pandas==2.0.3
openpyxl==3.1.2
drf-spectacular==0.27.1
djangorestframework-simplejwt==5.3.1
EOF

# ========================================
# CREER STRUCTURE DJANGO
# ========================================
mkdir -p mycar core/templates core/migrations core/management/commands

# ========================================
# FICHIER 5: manage.py
# ========================================
cat <<'EOF' > manage.py
#!/usr/bin/env python
import os
import sys
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycar.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
EOF
chmod +x manage.py

# ========================================
# FICHIER 6: mycar/__init__.py
# ========================================
touch mycar/__init__.py

# ========================================
# FICHIER 7: mycar/settings.py
# ========================================
cat <<'EOF' > mycar/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mycar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'mycar.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'mycar_local'),
        'USER': os.getenv('DB_USER', 'mycar_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'localpass123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Simple JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Niamey'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mock services for local dev
MOCK_SERVICES = os.getenv('MOCK_SERVICES', 'True') == 'True'
EOF

# ========================================
# FICHIER 8: mycar/urls.py
# ========================================
cat <<'EOF' > mycar/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('core.urls')),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
EOF

# ========================================
# FICHIER 9: mycar/wsgi.py
# ========================================
cat <<'EOF' > mycar/wsgi.py
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycar.settings')
application = get_wsgi_application()
EOF

# ========================================
# FICHIER 10: core/__init__.py
# ========================================
touch core/__init__.py

# ========================================
# FICHIER 11: core/apps.py
# ========================================
cat <<'EOF' > core/apps.py
from django.apps import AppConfig
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
EOF

# ========================================
# FICHIER 12: core/models.py
# ========================================
cat <<'EOF' > core/models.py
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.crypto import get_random_string
from django.utils import timezone

# Enums
class RoleUtilisateur(models.TextChoices):
    ADMIN_SYS = 'ADMINISTRATEUR_SYSTEME', 'Administrateur Système'
    SUP_DGI = 'SUPERVISEUR_DGI', 'Superviseur DGI'
    AGENT_DGI = 'AGENT_DGI', 'Agent DGI'
    POLICE = 'POLICE', 'Police'
    CONTRIBUABLE = 'CONTRIBUABLE', 'Contribuable'

class TypeVehicule(models.TextChoices):
    VEHICULE = 'VEHICULE', 'Véhicule'
    MOTO = 'MOTO', 'Moto'

class Energie(models.TextChoices):
    ESSENCE = 'ESSENCE', 'Essence'
    DIESEL = 'DIESEL', 'Diesel'

class StatutVignette(models.TextChoices):
    VERT = 'VERT', 'Vert - Valide'
    ORANGE = 'ORANGE', 'Orange - Échéance imminente'
    ROUGE = 'ROUGE', 'Rouge - Expiré'

class TypeModification(models.TextChoices):
    AUTO = 'AUTOMATIQUE', 'Automatique'
    MANUELLE = 'MANUELLE', 'Manuelle'

# Managers
class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('role', RoleUtilisateur.ADMIN_SYS)
        return self.create_user(email, password, **extra_fields)

# Models
class Region(models.Model):
    nom_region = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.nom_region

class Utilisateur(AbstractBaseUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=RoleUtilisateur.choices)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    structure_id = models.IntegerField(null=True, blank=True)
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    objects = UtilisateurManager()
    def __str__(self): return f"{self.nom} {self.prenom} ({self.role})"

class Automobile(models.Model):
    immatriculation = models.CharField(max_length=20)
    pays = models.CharField(max_length=100, default='NIGER')
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    type_vehicule = models.CharField(max_length=20, choices=TypeVehicule.choices)
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100, blank=True)
    energie = models.CharField(max_length=20, choices=Energie.choices, null=True)
    puissance_cv = models.IntegerField()
    montant_taxe = models.DecimalField(max_digits=10, decimal_places=2)
    numero_chassis = models.CharField(max_length=50, unique=True)
    date_mise_circulation = models.DateField(null=True)
    date_edition_carte_grise = models.DateField(null=True)
    statut_actuel = models.ForeignKey('StatutVignette', null=True, blank=True, on_delete=models.SET_NULL, related_name='current_auto')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['immatriculation', 'region']]
    
    def generer_qr_data(self):
        return {
            "v": "1.0",
            "immat": self.immatriculation,
            "region": self.region.nom_region,
            "chassis": self.numero_chassis,
            "proprietaire": f"{self.nom} {self.prenom}",
            "statut": self.statut_actuel.statut if self.statut_actuel else 'ROUGE',
            "validite_debut": self.statut_actuel.date_debut_validite.isoformat() if self.statut_actuel else None,
            "validite_fin": self.statut_actuel.date_fin_validite.isoformat() if self.statut_actuel else None,
            "montant": float(self.montant_taxe),
        }

class StatutVignette(models.Model):
    automobile = models.ForeignKey(Automobile, on_delete=models.CASCADE, related_name='statuts')
    statut = models.CharField(max_length=20, choices=StatutVignette.choices)
    date_debut_validite = models.DateField()
    date_fin_validite = models.DateField()
    code_securite = models.CharField(max_length=16, unique=True)
    type_modification = models.CharField(max_length=20, choices=TypeModification.choices)
    operateur = models.ForeignKey(Utilisateur, null=True, on_delete=models.SET_NULL)
    mobile_payment_ref = models.CharField(max_length=255, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.code_securite:
            self.code_securite = get_random_string(16, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        super().save(*args, **kwargs)

class CodeSecurite(models.Model):
    code = models.CharField(max_length=16, unique=True)
    statut_usage = models.CharField(max_length=20, default='ACTIF', choices=[('ACTIF', 'Actif'), ('UTILISE', 'Utilisé')])
    date_generation = models.DateTimeField(auto_now_add=True)
    automobile = models.ForeignKey(Automobile, on_delete=models.CASCADE)
    generateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_utilisation = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.code:
            raw = get_random_string(16, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.code = f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
        super().save(*args, **kwargs)

class HistoriqueConsultation(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, null=True, on_delete=models.SET_NULL)
    automobile = models.ForeignKey(Automobile, on_delete=models.CASCADE)
    date_consultation = models.DateTimeField(auto_now_add=True)
    action_performee = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
EOF

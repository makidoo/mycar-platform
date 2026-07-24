from django.contrib import admin
from django.conf import settings
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.static import serve as serve_media
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('core.urls')),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Frontend
    path('', TemplateView.as_view(template_name='login.html'), name='login'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('vehicules/', TemplateView.as_view(template_name='vehicules.html'), name='vehicules'),
    path('vehicules/<int:pk>/', TemplateView.as_view(template_name='vehicule_detail.html'), name='vehicule_detail'),
    path('verification/', TemplateView.as_view(template_name='verification.html'), name='verification'),
    path('saisie/', TemplateView.as_view(template_name='saisie.html'), name='saisie'),
    path('contribuable/', TemplateView.as_view(template_name='contribuable.html'), name='contribuable'),
    path('panel/utilisateurs/', TemplateView.as_view(template_name='panel_utilisateurs.html'), name='panel_utilisateurs'),
    path('panel/parametres/',   TemplateView.as_view(template_name='panel_parametres.html'),   name='panel_parametres'),
    path('vehicules/<int:pk>/certificat/', TemplateView.as_view(template_name='certificat.html'), name='certificat'),
    path('distribution/', TemplateView.as_view(template_name='agent_distribution.html'), name='agent_distribution'),
    path('transferts/',   TemplateView.as_view(template_name='transferts.html'),         name='transferts'),
    path('plaintes/',     TemplateView.as_view(template_name='plaintes.html'),           name='plaintes'),
    path('rapports/',      TemplateView.as_view(template_name='rapports.html'),       name='rapports'),
    path('journal-audit/', TemplateView.as_view(template_name='journal_audit.html'), name='journal_audit'),
    path('simulateur/',    TemplateView.as_view(template_name='simulateur.html'),    name='simulateur'),

    # Fichiers médias (photos de carte grise, etc.) — pas de nginx devant l'app,
    # donc Django sert lui-même ce volume, sans être limité au mode DEBUG.
    re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
]

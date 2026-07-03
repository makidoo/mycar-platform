from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    MyCarTokenObtainPairView, me,
    UtilisateurViewSet, RegionViewSet, AutomobileViewSet,
    StatutVignetteViewSet, CodeSecuriteViewSet, HistoriqueConsultationViewSet,
    AdminUtilisateurViewSet, ParametrePlateformeViewSet,
    DemandeTransfertViewSet, PlainteViewSet, JournalAuditViewSet, PermissionSpecialeViewSet,
    generer_code_securite, modifier_statut, approuver_vehicule,
    agent_rechercher_vehicule, agent_attribuer_vignette, agent_paiement_agence,
    certificat_vignette, export_excel,
    dashboard_superviseur, dashboard_financier, health_check,
    public_demander_otp, public_verifier_otp,
    public_initier_paiement, public_confirmer_paiement,
    log_inspection_gps,
)

router = DefaultRouter()
router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateur')
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'automobiles', AutomobileViewSet, basename='automobile')
router.register(r'statuts', StatutVignetteViewSet, basename='statut')
router.register(r'codes-securite', CodeSecuriteViewSet, basename='code-securite')
router.register(r'historique', HistoriqueConsultationViewSet, basename='historique')
router.register(r'admin/utilisateurs', AdminUtilisateurViewSet,   basename='admin-utilisateur')
router.register(r'admin/parametres',   ParametrePlateformeViewSet, basename='admin-parametre')
router.register(r'transferts',         DemandeTransfertViewSet,    basename='transfert')
router.register(r'plaintes',           PlainteViewSet,             basename='plainte')
router.register(r'journal-audit',      JournalAuditViewSet,        basename='journal-audit')
router.register(r'permissions',        PermissionSpecialeViewSet,  basename='permission')

urlpatterns = [
    path('auth/login/', MyCarTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', me, name='me'),
    path('automobiles/<int:automobile_id>/generer-code/', generer_code_securite,  name='generer_code_securite'),
    path('automobiles/<int:automobile_id>/approuver/',   approuver_vehicule,      name='approuver_vehicule'),
    path('automobiles/<int:automobile_id>/certificat/', certificat_vignette,      name='certificat_vignette'),
    path('export/excel/',                               export_excel,              name='export_excel'),
    path('agent/rechercher/',                           agent_rechercher_vehicule, name='agent_rechercher'),
    path('agent/attribuer/<int:automobile_id>/',        agent_attribuer_vignette,  name='agent_attribuer'),
    path('agent/paiement/<int:automobile_id>/',         agent_paiement_agence,     name='agent_paiement_agence'),
    path('statuts/modifier/', modifier_statut, name='modifier_statut'),
    path('dashboard/', dashboard_superviseur, name='dashboard'),
    path('dashboard/financier/', dashboard_financier, name='dashboard_financier'),
    path('health/', health_check, name='health_check'),

    # Portail public contribuable
    path('public/otp/demander/',                          public_demander_otp,       name='public_demander_otp'),
    path('public/otp/verifier/',                          public_verifier_otp,       name='public_verifier_otp'),
    path('public/paiement/initier/',                      public_initier_paiement,   name='public_initier_paiement'),
    path('public/paiement/<str:reference>/confirmer/',    public_confirmer_paiement, name='public_confirmer_paiement'),
    path('police/inspection/',                            log_inspection_gps,        name='log_inspection_gps'),
    path('', include(router.urls)),
]

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
import qrcode
import json
import base64
import io
from datetime import timedelta

from .models import (
    Automobile, Region, Utilisateur, RoleUtilisateur,
    StatutVignette, StatutVignetteChoix, CodeSecurite, HistoriqueConsultation,
    Paiement, StatutPaiement, OperateurPaiement, OTPVerification,
    ParametrePlateforme,
)
import random
from .serializers import (
    AutomobileReadSerializer, AutomobileWriteSerializer,
    RegionSerializer, UtilisateurSerializer, UtilisateurCreateSerializer,
    UtilisateurUpdateSerializer, ParametrePlateformeSerializer,
    StatutVignetteSerializer, CodeSecuriteSerializer, HistoriqueConsultationSerializer,
    PaiementSerializer,
)
from .permissions import AdminOnlyPermission, RoleBasedPermission


# =============== AUTH ===============

class MyCarTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role']       = user.role
        token['nom']        = user.nom
        token['prenom']     = user.prenom
        token['email']      = user.email
        token['region_id']  = user.region_id
        token['region_nom'] = user.region.nom_region if user.region else None
        return token

class MyCarTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyCarTokenSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    serializer = UtilisateurSerializer(request.user)
    return Response(serializer.data)


class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    permission_classes = [AdminOnlyPermission]

    def get_serializer_class(self):
        if self.action == 'create':
            return UtilisateurCreateSerializer
        return UtilisateurSerializer


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [IsAuthenticated]


class AutomobileViewSet(viewsets.ModelViewSet):
    queryset = Automobile.objects.select_related('region', 'statut_actuel').all()
    permission_classes = [RoleBasedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['immatriculation', 'nom', 'prenom', 'numero_chassis', 'marque']
    ordering_fields = ['date_creation', 'immatriculation']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AutomobileWriteSerializer
        return AutomobileReadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Agent DGI : restreint à sa région
        if user.role == RoleUtilisateur.AGENT_DGI and user.region_id:
            qs = qs.filter(region_id=user.region_id)

        region = self.request.query_params.get('region')
        statut = self.request.query_params.get('statut')
        type_vehicule = self.request.query_params.get('type_vehicule')
        if region:
            qs = qs.filter(region__nom_region__iexact=region)
        if statut:
            qs = qs.filter(statut_actuel__statut__iexact=statut)
        if type_vehicule:
            qs = qs.filter(type_vehicule__iexact=type_vehicule)
        return qs

    @action(detail=True, methods=['get'])
    def generer_qr(self, request, pk=None):
        automobile = self.get_object()
        qr_data = automobile.generer_qr_data()
        qr = qrcode.QRCode(
            version=10,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({'qr_code_base64': qr_base64, 'qr_data': qr_data})

    @action(detail=True, methods=['get'])
    def statuts(self, request, pk=None):
        """Historique des statuts d'un véhicule"""
        automobile = self.get_object()
        statuts = automobile.statuts.order_by('-date_creation')
        serializer = StatutVignetteSerializer(statuts, many=True)
        return Response(serializer.data)


class StatutVignetteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StatutVignette.objects.select_related('automobile', 'operateur').all()
    serializer_class = StatutVignetteSerializer
    permission_classes = [RoleBasedPermission]


class CodeSecuriteViewSet(viewsets.ModelViewSet):
    queryset = CodeSecurite.objects.select_related('automobile', 'generateur').all()
    serializer_class = CodeSecuriteSerializer
    permission_classes = [RoleBasedPermission]

    def perform_create(self, serializer):
        serializer.save(generateur=self.request.user)


class HistoriqueConsultationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HistoriqueConsultation.objects.select_related('utilisateur', 'automobile').all()
    serializer_class = HistoriqueConsultationSerializer
    permission_classes = [RoleBasedPermission]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-date_consultation']


# =============== CODE SÉCURITÉ ===============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generer_code_securite(request, automobile_id):
    """Génère un CodeSecurite usage unique pour un véhicule (Agent DGI / Superviseur / Admin)."""
    roles_autorises = {
        RoleUtilisateur.AGENT_DGI,
        RoleUtilisateur.SUP_DGI,
        RoleUtilisateur.ADMIN_SYS,
    }
    if request.user.role not in roles_autorises:
        return Response({'error': 'Accès non autorisé.'}, status=403)

    try:
        auto = Automobile.objects.get(id=automobile_id)
    except Automobile.DoesNotExist:
        return Response({'error': 'Véhicule introuvable.'}, status=404)

    # Invalider les codes actifs précédents pour ce véhicule
    CodeSecurite.objects.filter(automobile=auto, statut_usage='ACTIF').update(statut_usage='UTILISE')

    code = CodeSecurite.objects.create(automobile=auto, generateur=request.user)

    return Response({
        'code':        code.code,
        'automobile':  auto.immatriculation,
        'generateur':  f"{request.user.nom} {request.user.prenom}",
        'expire_apres': '30 minutes (usage unique)',
    }, status=201)


# =============== STATUTS ===============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def modifier_statut(request):
    """Modification manuelle du statut via code sécurité"""
    immatriculation = request.data.get('immatriculation')
    region_nom = request.data.get('region')
    code = request.data.get('code_securite')
    nouveau_statut = request.data.get('nouveau_statut', StatutVignetteChoix.VERT)

    if not all([immatriculation, region_nom, code]):
        return Response({'error': 'Champs obligatoires : immatriculation, region, code_securite'}, status=400)

    try:
        auto = Automobile.objects.get(
            immatriculation=immatriculation,
            region__nom_region__iexact=region_nom,
        )
    except Automobile.DoesNotExist:
        return Response({'error': 'Véhicule non trouvé'}, status=404)

    try:
        code_obj = CodeSecurite.objects.get(automobile=auto, code=code, statut_usage='ACTIF')
    except CodeSecurite.DoesNotExist:
        return Response({'error': 'Code sécurité invalide ou déjà utilisé'}, status=403)

    if nouveau_statut not in StatutVignetteChoix.values:
        return Response({'error': f'Statut invalide. Valeurs acceptées : {StatutVignetteChoix.values}'}, status=400)

    statut = StatutVignette.objects.create(
        automobile=auto,
        statut=nouveau_statut,
        date_debut_validite=timezone.now().date(),
        date_fin_validite=timezone.now().date() + timedelta(days=365),
        type_modification='MANUELLE',
        operateur=request.user,
    )
    auto.statut_actuel = statut
    auto.save(update_fields=['statut_actuel'])

    # Marquer le code comme utilisé
    code_obj.statut_usage = 'UTILISE'
    code_obj.date_utilisation = timezone.now()
    code_obj.save(update_fields=['statut_usage', 'date_utilisation'])

    return Response({'success': True, 'nouveau_statut': statut.statut})


# =============== DASHBOARD ===============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_superviseur(request):
    qs = Automobile.objects.all()
    if request.user.role == RoleUtilisateur.AGENT_DGI and request.user.region_id:
        qs = qs.filter(region_id=request.user.region_id)

    stats = qs.aggregate(
        total_verts=Count('id', filter=Q(statut_actuel__statut='VERT')),
        total_oranges=Count('id', filter=Q(statut_actuel__statut='ORANGE')),
        total_rouges=Count('id', filter=Q(statut_actuel__statut='ROUGE')),
        total=Count('id'),
    )
    return Response(stats)


# =============== ADMIN — UTILISATEURS ===============

class AdminUtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all().order_by('role', 'nom')
    permission_classes = [AdminOnlyPermission]

    def get_serializer_class(self):
        if self.action == 'create':
            return UtilisateurCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UtilisateurUpdateSerializer
        return UtilisateurSerializer

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('password', '').strip()
        if len(new_password) < 8:
            return Response({'error': 'Le mot de passe doit contenir au moins 8 caractères.'}, status=400)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'success': True, 'message': 'Mot de passe réinitialisé.'})

    @action(detail=False, methods=['post'])
    def change_my_password(self, request):
        ancien = request.data.get('ancien_password', '')
        nouveau = request.data.get('nouveau_password', '').strip()
        if not request.user.check_password(ancien):
            return Response({'error': 'Ancien mot de passe incorrect.'}, status=400)
        if len(nouveau) < 8:
            return Response({'error': 'Le nouveau mot de passe doit contenir au moins 8 caractères.'}, status=400)
        request.user.set_password(nouveau)
        request.user.save(update_fields=['password'])
        return Response({'success': True, 'message': 'Mot de passe modifié. Veuillez vous reconnecter.'})


# =============== ADMIN — PARAMÈTRES ===============

PARAMETRES_DEFAUT = [
    ('dashboard_roles',    'SUPERVISEUR_DGI,ADMINISTRATEUR_SYSTEME',                         'Rôles pouvant accéder au dashboard'),
    ('vehicules_roles',    'AGENT_DGI,SUPERVISEUR_DGI,ADMINISTRATEUR_SYSTEME,POLICE',        'Rôles pouvant voir la liste des véhicules'),
    ('saisie_roles',       'AGENT_DGI,SUPERVISEUR_DGI,ADMINISTRATEUR_SYSTEME',               'Rôles pouvant enregistrer un véhicule'),
    ('verification_roles', 'POLICE,AGENT_DGI,SUPERVISEUR_DGI,ADMINISTRATEUR_SYSTEME',        'Rôles pouvant accéder à la vérification'),
    ('nom_plateforme',     'MY CAR',                                                          'Nom affiché de la plateforme'),
    ('nom_organisation',   'DGI — République du Niger',                                       'Nom de l\'organisation'),
    ('devise',             'FCFA',                                                             'Devise utilisée pour les montants'),
    ('duree_vignette_jours', '365',                                                            'Durée de validité d\'une vignette (en jours)'),
    ('otp_expiration_minutes', '10',                                                           'Durée de validité d\'un OTP (en minutes)'),
]

class ParametrePlateformeViewSet(viewsets.ModelViewSet):
    queryset = ParametrePlateforme.objects.all().order_by('cle')
    serializer_class = ParametrePlateformeSerializer
    permission_classes = [AdminOnlyPermission]

    @action(detail=False, methods=['get'])
    def publics(self, request):
        """Paramètres lisibles par tous les utilisateurs authentifiés (nom plateforme, devise…)."""
        cles_publiques = ['nom_plateforme', 'nom_organisation', 'devise']
        params = ParametrePlateforme.objects.filter(cle__in=cles_publiques)
        return Response({p.cle: p.valeur for p in params})


# =============== PORTAIL CONTRIBUABLE (PUBLIC) ===============

def _masquer_telephone(tel):
    """Ex: +22790000001 → +227 90••••01"""
    t = tel.replace(' ', '')
    if len(t) >= 4:
        return t[:-6] + '••••' + t[-2:]
    return '••••••'


@api_view(['POST'])
@permission_classes([])
def public_demander_otp(request):
    """
    Étape 1 : le propriétaire saisit son immatriculation.
    Le système envoie un OTP sur le téléphone enregistré en base.
    Données personnelles NON exposées — seul le téléphone masqué est retourné.
    """
    immat  = request.data.get('immatriculation', '').strip().upper()
    region = request.data.get('region', '').strip()

    if not immat:
        return Response({'error': 'Immatriculation requise.'}, status=400)

    qs = Automobile.objects.select_related('region', 'statut_actuel').filter(immatriculation__iexact=immat)
    if region:
        qs = qs.filter(region__nom_region__iexact=region)
    auto = qs.first()

    if not auto:
        return Response({'error': 'Véhicule introuvable. Vérifiez l\'immatriculation et la région.'}, status=404)

    # Invalider les OTP précédents non utilisés
    OTPVerification.objects.filter(automobile=auto, est_utilise=False).update(est_utilise=True)

    code = f"{random.randint(0, 999999):06d}"
    otp  = OTPVerification.objects.create(
        automobile=auto,
        code=code,
        date_expiration=timezone.now() + timedelta(minutes=10),
    )

    # En production : envoyer le SMS ici via API opérateur
    # Simulation : on retourne le code en clair pour la démo

    return Response({
        'otp_id':           otp.id,
        'telephone_masque': _masquer_telephone(auto.telephone),
        'expires_in':       600,
        # --- DÉMO SEULEMENT — à supprimer en production ---
        'demo_code':        code,
        'demo_notice':      'En production, ce code serait envoyé par SMS uniquement.',
    }, status=200)


@api_view(['POST'])
@permission_classes([])
def public_verifier_otp(request):
    """
    Étape 2 : vérification du code OTP.
    Si valide → retourne un session_token (15 min) + les données du véhicule.
    """
    otp_id = request.data.get('otp_id')
    code   = request.data.get('code', '').strip()

    if not all([otp_id, code]):
        return Response({'error': 'otp_id et code requis.'}, status=400)

    try:
        otp = OTPVerification.objects.select_related('automobile__region', 'automobile__statut_actuel').get(id=otp_id)
    except OTPVerification.DoesNotExist:
        return Response({'error': 'Session OTP introuvable.'}, status=404)

    if not otp.est_valide():
        return Response({'error': 'Code expiré ou déjà utilisé. Veuillez recommencer.'}, status=400)

    if otp.code != code:
        return Response({'error': 'Code incorrect. Vérifiez le SMS reçu.'}, status=400)

    otp.est_utilise = True
    otp.save(update_fields=['est_utilise'])

    auto = otp.automobile
    s    = auto.statut_actuel

    return Response({
        'session_token': otp.session_token,
        'expires_in':    900,
        'vehicule': {
            'id':              auto.id,
            'immatriculation': auto.immatriculation,
            'region':          auto.region.nom_region,
            'proprietaire':    f"{auto.nom} {auto.prenom}",
            'marque':          f"{auto.marque} {auto.modele or ''}".strip(),
            'type_vehicule':   auto.type_vehicule,
            'montant_taxe':    float(auto.montant_taxe),
            'statut':          s.statut if s else 'ROUGE',
            'date_fin_validite': s.date_fin_validite.isoformat() if s else None,
        },
    })


@api_view(['POST'])
@permission_classes([])
def public_initier_paiement(request):
    """Initie un paiement mobile money (simulation). Requiert un session_token valide."""
    session_token = request.data.get('session_token', '').strip()
    operateur     = request.data.get('operateur')
    telephone     = request.data.get('telephone', '').strip()

    if not all([session_token, operateur, telephone]):
        return Response({'error': 'Champs requis : session_token, operateur, telephone.'}, status=400)

    if operateur not in OperateurPaiement.values:
        return Response({'error': f'Opérateur invalide.'}, status=400)

    try:
        otp = OTPVerification.objects.select_related('automobile').get(
            session_token=session_token,
            est_utilise=True,
            date_expiration__gte=timezone.now() - timedelta(minutes=15),
        )
    except OTPVerification.DoesNotExist:
        return Response({'error': 'Session expirée ou invalide. Veuillez vous réauthentifier.'}, status=403)

    # Un seul paiement autorisé par session OTP
    if hasattr(otp, 'paiement'):
        return Response({'error': 'Un paiement a déjà été initié pour cette session. Veuillez recommencer.'}, status=400)

    auto = otp.automobile
    Paiement.objects.filter(automobile=auto, statut=StatutPaiement.EN_ATTENTE).update(statut=StatutPaiement.ECHOUE)

    paiement = Paiement.objects.create(
        automobile=auto,
        otp=otp,
        montant=auto.montant_taxe,
        operateur=operateur,
        telephone=telephone,
    )

    return Response({
        'reference': paiement.reference,
        'montant':   float(paiement.montant),
        'operateur': paiement.operateur,
        'telephone': paiement.telephone,
        'statut':    paiement.statut,
        'message':   f'Demande envoyée. Confirmez sur votre téléphone.',
    }, status=201)


@api_view(['POST'])
@permission_classes([])
def public_confirmer_paiement(request, reference):
    """Simule la confirmation de paiement par l'opérateur mobile money."""
    try:
        paiement = Paiement.objects.select_related('automobile__region').get(reference=reference)
    except Paiement.DoesNotExist:
        return Response({'error': 'Référence de paiement introuvable.'}, status=404)

    if paiement.statut == StatutPaiement.CONFIRME:
        return Response({'error': 'Ce paiement est déjà confirmé.'}, status=400)

    if paiement.statut == StatutPaiement.ECHOUE:
        return Response({'error': 'Ce paiement a échoué. Veuillez recommencer.'}, status=400)

    # Simulation : création de la nouvelle vignette VERT
    auto = paiement.automobile
    sv = StatutVignette.objects.create(
        automobile=auto,
        statut=StatutVignetteChoix.VERT,
        date_debut_validite=timezone.now().date(),
        date_fin_validite=timezone.now().date() + timedelta(days=365),
        type_modification='AUTOMATIQUE',
        operateur=None,
        mobile_payment_ref=paiement.reference,
    )
    auto.statut_actuel = sv
    auto.save(update_fields=['statut_actuel'])

    paiement.statut           = StatutPaiement.CONFIRME
    paiement.date_confirmation = timezone.now()
    paiement.statut_vignette  = sv
    paiement.save()

    # Générer QR
    qr_data = auto.generer_qr_data()
    qr = qrcode.QRCode(version=10, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=3)
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return Response({
        'statut':          'CONFIRME',
        'reference':       paiement.reference,
        'montant':         float(paiement.montant),
        'operateur':       paiement.operateur,
        'date_confirmation': paiement.date_confirmation.isoformat(),
        'vignette': {
            'statut':            sv.statut,
            'date_debut':        sv.date_debut_validite.isoformat(),
            'date_fin':          sv.date_fin_validite.isoformat(),
            'code_securite':     sv.code_securite,
        },
        'qr_code_base64': qr_b64,
        'qr_data':        qr_data,
    })


# =============== DASHBOARD FINANCIER ===============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_financier(request):
    """
    Agrégation des paiements confirmés avec filtres :
    date_debut, date_fin, region, agent (utilisateur_id)
    """
    from django.db.models.functions import TruncMonth, TruncDay
    from django.db.models import Sum, Count, Q
    import csv
    from django.http import HttpResponse as DjangoHttpResponse

    qs = Paiement.objects.filter(statut=StatutPaiement.CONFIRME).select_related(
        'automobile__region', 'otp'
    )

    # Agent DGI : restreint à sa région
    if request.user.role == RoleUtilisateur.AGENT_DGI and request.user.region_id:
        qs = qs.filter(automobile__region_id=request.user.region_id)

    # Filtres
    date_debut = request.query_params.get('date_debut')
    date_fin   = request.query_params.get('date_fin')
    region     = request.query_params.get('region')
    operateur  = request.query_params.get('operateur')

    if date_debut:
        qs = qs.filter(date_confirmation__date__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_confirmation__date__lte=date_fin)
    if region:
        qs = qs.filter(automobile__region__nom_region__iexact=region)
    if operateur:
        qs = qs.filter(operateur=operateur)

    # Totaux globaux
    totaux = qs.aggregate(
        total_recettes=Sum('montant'),
        total_paiements=Count('id'),
    )

    # Par mois
    par_mois = list(
        qs.annotate(mois=TruncMonth('date_confirmation'))
          .values('mois')
          .annotate(recettes=Sum('montant'), nb=Count('id'))
          .order_by('mois')
    )

    # Par région
    par_region = list(
        qs.values('automobile__region__nom_region')
          .annotate(recettes=Sum('montant'), nb=Count('id'))
          .order_by('-recettes')
    )

    # Par opérateur mobile money
    par_operateur = list(
        qs.values('operateur')
          .annotate(recettes=Sum('montant'), nb=Count('id'))
          .order_by('-recettes')
    )

    # Derniers paiements
    derniers = list(
        qs.order_by('-date_confirmation')[:20]
          .values(
              'reference', 'montant', 'operateur', 'date_confirmation',
              'automobile__immatriculation', 'automobile__region__nom_region',
          )
    )

    # Export CSV
    if request.query_params.get('export') == 'csv':
        response = DjangoHttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="recettes_mycar.csv"'
        writer = csv.writer(response)
        writer.writerow(['Référence', 'Immatriculation', 'Région', 'Opérateur', 'Montant (FCFA)', 'Date'])
        for p in qs.order_by('-date_confirmation').values(
            'reference', 'automobile__immatriculation',
            'automobile__region__nom_region', 'operateur', 'montant', 'date_confirmation'
        ):
            writer.writerow([
                p['reference'],
                p['automobile__immatriculation'],
                p['automobile__region__nom_region'],
                p['operateur'],
                p['montant'],
                p['date_confirmation'].strftime('%d/%m/%Y %H:%M') if p['date_confirmation'] else '',
            ])
        return response

    return Response({
        'totaux': {
            'recettes':   float(totaux['total_recettes'] or 0),
            'paiements':  totaux['total_paiements'],
        },
        'par_mois': [
            {'mois': e['mois'].strftime('%Y-%m'), 'recettes': float(e['recettes']), 'nb': e['nb']}
            for e in par_mois
        ],
        'par_region': [
            {'region': e['automobile__region__nom_region'], 'recettes': float(e['recettes']), 'nb': e['nb']}
            for e in par_region
        ],
        'par_operateur': [
            {'operateur': e['operateur'], 'recettes': float(e['recettes']), 'nb': e['nb']}
            for e in par_operateur
        ],
        'derniers_paiements': [
            {
                'reference':      p['reference'],
                'immatriculation': p['automobile__immatriculation'],
                'region':         p['automobile__region__nom_region'],
                'operateur':      p['operateur'],
                'montant':        float(p['montant']),
                'date':           p['date_confirmation'].strftime('%d/%m/%Y %H:%M') if p['date_confirmation'] else '',
            }
            for p in derniers
        ],
    })


# =============== HEALTH CHECK ===============

@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok', 'timestamp': timezone.now()}, status=200)

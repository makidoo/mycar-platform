import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.crypto import get_random_string
from django.utils import timezone


class RoleUtilisateur(models.TextChoices):
    ADMIN_SYS        = 'ADMINISTRATEUR_SYSTEME',  'Administrateur Système'
    SUP_DGI          = 'SUPERVISEUR_DGI',          'Superviseur DGI'
    AGENT_DGI        = 'AGENT_DGI',                'Agent DGI'
    AGENT_DISTRIB    = 'AGENT_DISTRIBUTION',        'Agent de distribution'
    POLICE           = 'POLICE',                   'Police'
    CONTRIBUABLE     = 'CONTRIBUABLE',             'Contribuable'


class TypeVehicule(models.TextChoices):
    VEHICULE = 'VEHICULE', 'Véhicule'
    MOTO     = 'MOTO',     'Moto'
    BUS      = 'BUS',      'Bus'
    CAMION   = 'CAMION',   'Camion'


class Energie(models.TextChoices):
    ESSENCE = 'ESSENCE', 'Essence'
    DIESEL = 'DIESEL', 'Diesel'


class StatutVignetteChoix(models.TextChoices):
    VERT   = 'VERT',   'Vert - Valide'
    ORANGE = 'ORANGE', 'Orange - Échéance imminente'
    ROUGE  = 'ROUGE',  'Rouge - Expiré'


class StatutApprobationVehicule(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    APPROUVE   = 'APPROUVE',   'Approuvé'
    REJETE     = 'REJETE',     'Rejeté'
    SUSPENDU   = 'SUSPENDU',   'Suspendu'


class StatutPhysiqueVignette(models.TextChoices):
    NON_ATTRIBUE = 'NON_ATTRIBUE', 'Non attribué'
    ATTRIBUE     = 'ATTRIBUE',     'Attribué'


class TypeModification(models.TextChoices):
    AUTO = 'AUTOMATIQUE', 'Automatique'
    MANUELLE = 'MANUELLE', 'Manuelle'


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


class Region(models.Model):
    nom_region  = models.CharField(max_length=50, unique=True)
    code_region = models.CharField(max_length=5, unique=True, blank=True, default='')

    class Meta:
        ordering = ['nom_region']

    def __str__(self):
        return f"{self.nom_region} ({self.code_region})" if self.code_region else self.nom_region


class Utilisateur(AbstractBaseUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=RoleUtilisateur.choices)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    # Identifiant libre de l'agence partenaire (AGENT_DISTRIB) ou du bureau DGI (AGENT_DGI)
    # de rattachement. Pas de FK : aucun modèle Agence/Structure n'existe encore.
    structure_id = models.IntegerField(null=True, blank=True)
    region = models.ForeignKey(
        'Region', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='agents'
    )
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        return self.est_actif

    USERNAME_FIELD = 'email'
    objects = UtilisateurManager()

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.role})"


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
    annee_fabrication = models.IntegerField(null=True, blank=True)
    montant_taxe = models.DecimalField(max_digits=10, decimal_places=2)
    numero_chassis = models.CharField(max_length=50, unique=True)
    date_mise_circulation = models.DateField(null=True)
    date_edition_carte_grise = models.DateField(null=True)
    # Workflow d'approbation (Pending → Approved/Rejected/Suspended)
    statut_approbation = models.CharField(
        max_length=20,
        choices=StatutApprobationVehicule.choices,
        default=StatutApprobationVehicule.EN_ATTENTE,
    )
    notes_approbation = models.TextField(blank=True)
    statut_actuel = models.ForeignKey(
        'StatutVignette', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='current_auto'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['immatriculation', 'region']]
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.immatriculation} - {self.nom} {self.prenom}"

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
    statut = models.CharField(max_length=20, choices=StatutVignetteChoix.choices)
    date_debut_validite = models.DateField()
    date_fin_validite = models.DateField()
    code_securite = models.CharField(max_length=16, unique=True)
    type_modification = models.CharField(max_length=20, choices=TypeModification.choices)
    operateur = models.ForeignKey(Utilisateur, null=True, on_delete=models.SET_NULL)
    mobile_payment_ref = models.CharField(max_length=255, blank=True)
    # Suivi vignette physique
    statut_physique = models.CharField(
        max_length=20,
        choices=StatutPhysiqueVignette.choices,
        default=StatutPhysiqueVignette.NON_ATTRIBUE,
    )
    # Pour transitions manuelles : n° de reçu + notes obligatoires
    numero_recu = models.CharField(max_length=100, blank=True)
    notes_admin = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code_securite:
            self.code_securite = get_random_string(16, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.automobile.immatriculation} - {self.statut} ({self.date_fin_validite})"

    @property
    def est_valide(self):
        from django.utils import timezone
        return (
            self.statut == StatutVignetteChoix.VERT
            and self.date_fin_validite >= timezone.now().date()
        )


class CodeSecurite(models.Model):
    code = models.CharField(max_length=19, unique=True)  # format XXXX-XXXX-XXXX-XXXX
    statut_usage = models.CharField(
        max_length=20, default='ACTIF',
        choices=[('ACTIF', 'Actif'), ('UTILISE', 'Utilisé')]
    )
    date_generation = models.DateTimeField(auto_now_add=True)
    automobile = models.ForeignKey(Automobile, on_delete=models.CASCADE, related_name='codes_securite')
    generateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_utilisation = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            raw = get_random_string(16, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.code = f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.statut_usage})"


class OTPVerification(models.Model):
    automobile      = models.ForeignKey('Automobile', on_delete=models.CASCADE, related_name='otps')
    code            = models.CharField(max_length=6)
    session_token   = models.CharField(max_length=64, unique=True, blank=True)
    date_creation   = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    est_utilise     = models.BooleanField(default=False)

    def est_valide(self):
        return not self.est_utilise and timezone.now() < self.date_expiration

    def save(self, *args, **kwargs):
        if not self.session_token:
            self.session_token = get_random_string(64, 'abcdefghijklmnopqrstuvwxyz0123456789')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OTP {self.automobile.immatriculation} — {'utilisé' if self.est_utilise else 'actif'}"


class OperateurPaiement(models.TextChoices):
    NITA        = 'NITA',         'NITA'
    AMANATA     = 'AMANATA',      'Amanata'
    ORANGE      = 'ORANGE_MONEY', 'ZamaniCash'
    AIRTEL      = 'AIRTEL_MONEY', 'Airtel Money'
    CARTE       = 'CARTE_BANCAIRE', 'Carte bancaire'


class StatutPaiement(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    CONFIRME   = 'CONFIRME',   'Confirmé'
    ECHOUE     = 'ECHOUE',     'Échoué'


class Paiement(models.Model):
    reference         = models.CharField(max_length=30, unique=True)
    automobile        = models.ForeignKey(Automobile, on_delete=models.CASCADE, related_name='paiements')
    otp               = models.OneToOneField('OTPVerification', null=True, blank=True, on_delete=models.SET_NULL, related_name='paiement')
    montant           = models.DecimalField(max_digits=10, decimal_places=2)
    operateur         = models.CharField(max_length=20, choices=OperateurPaiement.choices)
    telephone         = models.CharField(max_length=20, blank=True, default='')
    # Renseignés uniquement pour un paiement par carte bancaire (simulation) — le numéro complet
    # n'est jamais stocké, seule sa version masquée l'est.
    carte_numero_masque = models.CharField(max_length=19, blank=True, default='')
    carte_expiration    = models.CharField(max_length=5, blank=True, default='')
    statut            = models.CharField(max_length=20, choices=StatutPaiement.choices, default=StatutPaiement.EN_ATTENTE)
    duree_annees      = models.IntegerField(default=1)
    date_initiation   = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    statut_vignette   = models.ForeignKey(
        'StatutVignette', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='paiement'
    )

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'PAY-' + get_random_string(12, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.automobile.immatriculation} — {self.statut}"


class ParametrePlateforme(models.Model):
    cle         = models.CharField(max_length=100, unique=True)
    valeur      = models.TextField()
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.cle} = {self.valeur}"


class StatutTransfert(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    APPROUVE   = 'APPROUVE',   'Approuvé'
    REJETE     = 'REJETE',     'Rejeté'


class DemandeTransfert(models.Model):
    """Demande de transfert de propriété d'un véhicule vers un nouveau propriétaire."""
    automobile        = models.ForeignKey(Automobile, on_delete=models.CASCADE, related_name='transferts')
    # Ancien propriétaire (extrait automatiquement du véhicule)
    ancien_nom        = models.CharField(max_length=100)
    ancien_prenom     = models.CharField(max_length=100)
    ancien_telephone  = models.CharField(max_length=20)
    # Nouveau propriétaire
    nouveau_nom       = models.CharField(max_length=100)
    nouveau_prenom    = models.CharField(max_length=100)
    nouveau_telephone = models.CharField(max_length=20)
    # Motif + documents
    motif             = models.TextField(blank=True)
    statut            = models.CharField(max_length=20, choices=StatutTransfert.choices, default=StatutTransfert.EN_ATTENTE)
    notes_admin       = models.TextField(blank=True)
    # Opérateur ayant traité
    traite_par        = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.SET_NULL, related_name='transferts_traites')
    date_demande      = models.DateTimeField(auto_now_add=True)
    date_traitement   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Transfert {self.automobile.immatriculation} → {self.nouveau_nom} {self.nouveau_prenom} ({self.statut})"


class StatutPlainte(models.TextChoices):
    OUVERTE   = 'OUVERTE',   'Ouverte'
    EN_COURS  = 'EN_COURS',  'En cours de traitement'
    RESOLUE   = 'RESOLUE',   'Résolue'
    REJETEE   = 'REJETEE',   'Rejetée'


class Plainte(models.Model):
    """Système de plaintes et litiges des contribuables."""
    reference        = models.CharField(max_length=20, unique=True, blank=True)
    automobile       = models.ForeignKey(Automobile, null=True, blank=True, on_delete=models.SET_NULL, related_name='plaintes')
    # Contact plaignant (pas nécessairement un utilisateur système)
    nom_plaignant    = models.CharField(max_length=100)
    telephone        = models.CharField(max_length=20)
    sujet            = models.CharField(max_length=200)
    description      = models.TextField()
    statut           = models.CharField(max_length=20, choices=StatutPlainte.choices, default=StatutPlainte.OUVERTE)
    reponse_admin    = models.TextField(blank=True)
    traite_par       = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.SET_NULL, related_name='plaintes_traitees')
    date_creation    = models.DateTimeField(auto_now_add=True)
    date_traitement  = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'PLT-' + get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.sujet[:50]} ({self.statut})"


class NotificationLog(models.Model):
    """Trace tous les SMS/emails envoyés (réels ou simulés)."""
    canal        = models.CharField(max_length=10, default='SMS')
    destinataire = models.CharField(max_length=50)
    message      = models.TextField()
    contexte     = models.CharField(max_length=100, blank=True)
    statut       = models.CharField(max_length=20, default='MOCK')
    date_envoi   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.canal}] {self.destinataire} — {self.contexte} ({self.statut})"



class HistoriqueConsultation(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, null=True, on_delete=models.SET_NULL)
    automobile = models.ForeignKey(Automobile, on_delete=models.CASCADE, related_name='historique')
    date_consultation = models.DateTimeField(auto_now_add=True)
    action_performee = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f"{self.automobile.immatriculation} - {self.action_performee[:50]}"


class CategorieAudit(models.TextChoices):
    CONNEXION    = 'CONNEXION',    'Connexion'
    VEHICULE     = 'VEHICULE',     'Véhicule'
    PAIEMENT     = 'PAIEMENT',     'Paiement'
    UTILISATEUR  = 'UTILISATEUR',  'Utilisateur'
    DISTRIBUTION = 'DISTRIBUTION', 'Distribution'
    TRANSFERT    = 'TRANSFERT',    'Transfert'
    PARAMETRES   = 'PARAMETRES',   'Paramètres'
    POLICE       = 'POLICE',       'Police'


class JournalAudit(models.Model):
    utilisateur       = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.SET_NULL, related_name='journal')
    utilisateur_email = models.CharField(max_length=255, blank=True)
    utilisateur_role  = models.CharField(max_length=50, blank=True)
    categorie         = models.CharField(max_length=20, choices=CategorieAudit.choices)
    action            = models.CharField(max_length=200)
    detail            = models.TextField(blank=True)
    objet_type        = models.CharField(max_length=50, blank=True)
    objet_id          = models.CharField(max_length=50, blank=True)
    objet_label       = models.CharField(max_length=200, blank=True)
    ip_address        = models.GenericIPAddressField(null=True, blank=True)
    date_action       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_action']

    def __str__(self):
        return f"[{self.categorie}] {self.utilisateur_email} — {self.action}"

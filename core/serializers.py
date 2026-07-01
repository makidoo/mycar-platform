from rest_framework import serializers
from .models import (
    Region, Utilisateur, Automobile,
    StatutVignette, CodeSecurite, HistoriqueConsultation, Paiement,
    ParametrePlateforme, DemandeTransfert, Plainte,
)


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'nom_region']


class UtilisateurSerializer(serializers.ModelSerializer):
    region_nom = serializers.CharField(source='region.nom_region', read_only=True)

    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'role', 'nom', 'prenom', 'structure_id', 'region', 'region_nom', 'est_actif', 'date_creation']
        read_only_fields = ['date_creation']


class UtilisateurCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'password', 'role', 'nom', 'prenom', 'structure_id', 'region']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StatutVignetteSerializer(serializers.ModelSerializer):
    est_valide = serializers.BooleanField(read_only=True)

    class Meta:
        model = StatutVignette
        fields = [
            'id', 'automobile', 'statut', 'date_debut_validite', 'date_fin_validite',
            'code_securite', 'type_modification', 'operateur', 'mobile_payment_ref',
            'statut_physique', 'numero_recu', 'notes_admin',
            'date_creation', 'est_valide',
        ]
        read_only_fields = ['code_securite', 'date_creation']


class DemandeTransfertSerializer(serializers.ModelSerializer):
    automobile_immat = serializers.CharField(source='automobile.immatriculation', read_only=True)
    traite_par_nom   = serializers.SerializerMethodField()

    class Meta:
        model = DemandeTransfert
        fields = [
            'id', 'automobile', 'automobile_immat',
            'ancien_nom', 'ancien_prenom', 'ancien_telephone',
            'nouveau_nom', 'nouveau_prenom', 'nouveau_telephone',
            'motif', 'statut', 'notes_admin',
            'traite_par', 'traite_par_nom',
            'date_demande', 'date_traitement',
        ]
        read_only_fields = ['statut', 'traite_par', 'date_demande', 'date_traitement']

    def get_traite_par_nom(self, obj):
        if obj.traite_par:
            return f"{obj.traite_par.nom} {obj.traite_par.prenom}"
        return None


class AutomobileReadSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    statut_actuel = StatutVignetteSerializer(read_only=True)

    class Meta:
        model = Automobile
        fields = [
            'id', 'immatriculation', 'pays', 'region', 'nom', 'prenom', 'telephone',
            'type_vehicule', 'marque', 'modele', 'energie', 'puissance_cv',
            'annee_fabrication', 'montant_taxe', 'numero_chassis',
            'date_mise_circulation', 'date_edition_carte_grise',
            'statut_approbation', 'notes_approbation',
            'statut_actuel', 'date_creation',
        ]


class AutomobileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Automobile
        fields = [
            'id', 'immatriculation', 'pays', 'region', 'nom', 'prenom', 'telephone',
            'type_vehicule', 'marque', 'modele', 'energie', 'puissance_cv',
            'annee_fabrication', 'montant_taxe', 'numero_chassis',
            'date_mise_circulation', 'date_edition_carte_grise',
        ]


class CodeSecuriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeSecurite
        fields = [
            'id', 'code', 'statut_usage', 'date_generation',
            'automobile', 'generateur', 'date_utilisation',
        ]
        read_only_fields = ['code', 'date_generation']


class UtilisateurUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'password', 'role', 'nom', 'prenom', 'structure_id', 'region', 'est_actif']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ParametrePlateformeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametrePlateforme
        fields = ['id', 'cle', 'valeur', 'description']


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = [
            'id', 'reference', 'automobile', 'montant', 'operateur',
            'telephone', 'statut', 'date_initiation', 'date_confirmation',
        ]
        read_only_fields = ['reference', 'statut', 'date_initiation', 'date_confirmation']


class PlainteSerializer(serializers.ModelSerializer):
    traite_par_nom = serializers.SerializerMethodField()
    automobile_immat = serializers.CharField(source='automobile.immatriculation', read_only=True)

    class Meta:
        model = Plainte
        fields = [
            'id', 'reference', 'automobile', 'automobile_immat',
            'nom_plaignant', 'telephone', 'sujet', 'description',
            'statut', 'reponse_admin', 'traite_par', 'traite_par_nom',
            'date_creation', 'date_traitement',
        ]
        read_only_fields = ['reference', 'statut', 'reponse_admin', 'traite_par', 'date_creation', 'date_traitement']

    def get_traite_par_nom(self, obj):
        if obj.traite_par:
            return f"{obj.traite_par.nom} {obj.traite_par.prenom}"
        return None


class HistoriqueConsultationSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer(read_only=True)
    automobile_immatriculation = serializers.CharField(
        source='automobile.immatriculation', read_only=True
    )

    class Meta:
        model = HistoriqueConsultation
        fields = [
            'id', 'utilisateur', 'automobile', 'automobile_immatriculation',
            'date_consultation', 'action_performee', 'ip_address',
        ]
        read_only_fields = ['date_consultation']

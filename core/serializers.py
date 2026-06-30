from rest_framework import serializers
from .models import (
    Region, Utilisateur, Automobile,
    StatutVignette, CodeSecurite, HistoriqueConsultation, Paiement,
    ParametrePlateforme,
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
            'date_creation', 'est_valide',
        ]
        read_only_fields = ['code_securite', 'date_creation']


class AutomobileReadSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    statut_actuel = StatutVignetteSerializer(read_only=True)

    class Meta:
        model = Automobile
        fields = [
            'id', 'immatriculation', 'pays', 'region', 'nom', 'prenom', 'telephone',
            'type_vehicule', 'marque', 'modele', 'energie', 'puissance_cv',
            'montant_taxe', 'numero_chassis', 'date_mise_circulation',
            'date_edition_carte_grise', 'statut_actuel', 'date_creation',
        ]


class AutomobileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Automobile
        fields = [
            'id', 'immatriculation', 'pays', 'region', 'nom', 'prenom', 'telephone',
            'type_vehicule', 'marque', 'modele', 'energie', 'puissance_cv',
            'montant_taxe', 'numero_chassis', 'date_mise_circulation',
            'date_edition_carte_grise',
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

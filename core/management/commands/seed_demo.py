from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Utilisateur, Region, Automobile, StatutVignette,
    StatutVignetteChoix, TypeModification, RoleUtilisateur,
    ParametrePlateforme, Paiement, StatutPaiement, OperateurPaiement,
)
from core.views import PARAMETRES_DEFAUT


REGIONS = ['Niamey', 'Zinder', 'Maradi', 'Tahoua', 'Agadez', 'Dosso', 'Tillabéri', 'Diffa']

CODES_REGIONS = {
    'Niamey':     'NIA',
    'Zinder':     'ZIN',
    'Maradi':     'MAR',
    'Tahoua':     'TAH',
    'Agadez':     'AGA',
    'Dosso':      'DOS',
    'Tillabéri':  'TIL',
    'Diffa':      'DIF',
}

VEHICULES = [
    ('NIA-001-A', 'Mahamadou', 'Issoufou',   '70000001', 'VEHICULE', 'Toyota',      'Hilux',       'DIESEL',  120, 25000, 'Niamey',    'VERT',   0),
    ('NIA-002-B', 'Aminatou',  'Moussa',      '70000002', 'VEHICULE', 'Nissan',      'Patrol',      'DIESEL',  150, 30000, 'Niamey',    'VERT',   0),
    ('ZIN-001-A', 'Ibrahim',   'Hamidou',     '70000003', 'VEHICULE', 'Mercedes',    'Sprinter',    'DIESEL',  95,  20000, 'Zinder',    'ORANGE', 320),
    ('ZIN-002-B', 'Fatouma',   'Abdou',       '70000004', 'MOTO',     'Yamaha',      'YBR125',      'ESSENCE', 10,  5000,  'Zinder',    'VERT',   0),
    ('MAR-001-A', 'Oumarou',   'Sani',        '70000005', 'VEHICULE', 'Toyota',      'Land Cruiser','DIESEL',  180, 35000, 'Maradi',    'ROUGE',  400),
    ('MAR-002-B', 'Halima',    'Maman',       '70000006', 'VEHICULE', 'Peugeot',     '504',         'ESSENCE', 70,  15000, 'Maradi',    'VERT',   0),
    ('TAH-001-A', 'Boubacar',  'Djibo',       '70000007', 'VEHICULE', 'Toyota',      'Corolla',     'ESSENCE', 90,  18000, 'Tahoua',    'ORANGE', 340),
    ('AGA-001-A', 'Adamou',    'Elhadji',     '70000008', 'MOTO',     'Honda',       'CB125',       'ESSENCE', 12,  5000,  'Agadez',    'ROUGE',  500),
    ('DOS-001-A', 'Ramatou',   'Hassoumi',    '70000009', 'VEHICULE', 'Renault',     'Duster',      'DIESEL',  85,  17000, 'Dosso',     'VERT',   0),
    ('NIA-003-C', 'Seyni',     'Oumarou',     '70000010', 'VEHICULE', 'Hyundai',     'H1',          'DIESEL',  130, 28000, 'Niamey',    'VERT',   0),
    ('NIA-004-D', 'Zeinabou',  'Ali',         '70000011', 'MOTO',     'Suzuki',      'GD110',       'ESSENCE', 11,  4500,  'Niamey',    'ROUGE',  600),
    ('TIL-001-A', 'Moussa',    'Garba',       '70000012', 'VEHICULE', 'Ford',        'Ranger',      'DIESEL',  160, 32000, 'Tillabéri', 'ORANGE', 355),
]

# (immatriculation, operateur, mois_retro) — mois_retro = il y a N mois
PAIEMENTS_DEMO = [
    ('NIA-001-A', 'NITA',         0),
    ('NIA-001-A', 'NITA',         1),
    ('NIA-001-A', 'ORANGE_MONEY', 2),
    ('NIA-002-B', 'AMANATA',      0),
    ('NIA-002-B', 'AMANATA',      1),
    ('NIA-003-C', 'NITA',         0),
    ('NIA-003-C', 'AIRTEL_MONEY', 3),
    ('ZIN-001-A', 'ORANGE_MONEY', 0),
    ('ZIN-001-A', 'NITA',         2),
    ('ZIN-002-B', 'AMANATA',      1),
    ('MAR-001-A', 'NITA',         0),
    ('MAR-001-A', 'ORANGE_MONEY', 1),
    ('MAR-002-B', 'AIRTEL_MONEY', 0),
    ('TAH-001-A', 'AMANATA',      2),
    ('DOS-001-A', 'NITA',         0),
    ('TIL-001-A', 'ORANGE_MONEY', 1),
]


class Command(BaseCommand):
    help = 'Insère des données de démonstration'

    def handle(self, *args, **options):
        self.stdout.write('Nettoyage des données existantes...')
        Paiement.objects.all().delete()
        StatutVignette.objects.all().delete()
        Automobile.objects.all().delete()
        Utilisateur.objects.all().delete()
        Region.objects.all().delete()

        # Régions
        regions = {nom: Region.objects.create(nom_region=nom, code_region=CODES_REGIONS[nom]) for nom in REGIONS}
        self.stdout.write(f'  {len(regions)} régions créées')

        # Utilisateurs
        admin = Utilisateur.objects.create_user(
            email='admin@mycar.ne', password='Admin1234!',
            role=RoleUtilisateur.ADMIN_SYS, nom='Admin', prenom='Système',
        )
        sup = Utilisateur.objects.create_user(
            email='superviseur@mycar.ne', password='Admin1234!',
            role=RoleUtilisateur.SUP_DGI, nom='Superviseur', prenom='DGI',
        )
        agent = Utilisateur.objects.create_user(
            email='agent@mycar.ne', password='Admin1234!',
            role=RoleUtilisateur.AGENT_DGI, nom='Agent', prenom='DGI',
            region=regions['Niamey'],
        )
        Utilisateur.objects.create_user(
            email='police@mycar.ne', password='Admin1234!',
            role=RoleUtilisateur.POLICE, nom='Officier', prenom='Police',
        )
        Utilisateur.objects.create_user(
            email='contribuable@mycar.ne', password='Admin1234!',
            role=RoleUtilisateur.CONTRIBUABLE, nom='Mahamadou', prenom='Issoufou',
        )
        Utilisateur.objects.create_user(
            email='distribution@mycar.ne', password='Admin1234!',
            role=RoleUtilisateur.AGENT_DISTRIB, nom='Agent', prenom='Distribution',
            region=regions['Niamey'],
        )
        self.stdout.write('  6 utilisateurs créés')

        # Véhicules
        now = timezone.now()
        autos_map = {}
        for i, (immat, nom, prenom, tel, type_v, marque, modele, energie, cv, taxe, region_nom, statut, delta) in enumerate(VEHICULES):
            auto = Automobile.objects.create(
                immatriculation=immat,
                region=regions[region_nom],
                nom=nom, prenom=prenom, telephone=tel,
                type_vehicule=type_v, marque=marque, modele=modele,
                energie=energie, puissance_cv=cv, montant_taxe=taxe,
                numero_chassis=f'CHASSIS{i+1:04d}',
                date_mise_circulation='2019-01-01',
            )
            date_fin = now.date() - timedelta(days=delta) if delta > 0 else now.date() + timedelta(days=365 - delta)
            sv = StatutVignette.objects.create(
                automobile=auto,
                statut=statut,
                date_debut_validite=date_fin - timedelta(days=365),
                date_fin_validite=date_fin,
                type_modification=TypeModification.AUTO,
                operateur=agent,
            )
            auto.statut_actuel = sv
            auto.save(update_fields=['statut_actuel'])
            autos_map[immat] = auto

        self.stdout.write(f'  {len(VEHICULES)} véhicules créés')

        # Paiements démo — répartis sur les derniers mois
        for immat, operateur, mois_retro in PAIEMENTS_DEMO:
            auto = autos_map.get(immat)
            if not auto:
                continue
            date_confirm = now - timedelta(days=mois_retro * 30 + (hash(immat + operateur) % 15))
            sv_pay = StatutVignette.objects.create(
                automobile=auto,
                statut=StatutVignetteChoix.VERT,
                date_debut_validite=date_confirm.date(),
                date_fin_validite=date_confirm.date() + timedelta(days=365),
                type_modification=TypeModification.AUTO,
                operateur=agent,
                mobile_payment_ref=f'DEMO-{immat}-{mois_retro}',
            )
            Paiement.objects.create(
                automobile=auto,
                montant=auto.montant_taxe,
                operateur=operateur,
                telephone=f'+227{auto.telephone}',
                statut=StatutPaiement.CONFIRME,
                date_confirmation=date_confirm,
                statut_vignette=sv_pay,
            )

        self.stdout.write(f'  {len(PAIEMENTS_DEMO)} paiements démo créés')

        # Paramètres plateforme
        ParametrePlateforme.objects.all().delete()
        for cle, valeur, description in PARAMETRES_DEFAUT:
            ParametrePlateforme.objects.create(cle=cle, valeur=valeur, description=description)
        self.stdout.write(f'  {len(PARAMETRES_DEFAUT)} paramètres initialisés')

        self.stdout.write(self.style.SUCCESS('\nDonnées démo prêtes !'))
        self.stdout.write('\nComptes disponibles :')
        self.stdout.write('  admin@mycar.ne          / Admin1234!  (Administrateur)')
        self.stdout.write('  superviseur@mycar.ne    / Admin1234!  (Superviseur DGI)')
        self.stdout.write('  agent@mycar.ne          / Admin1234!  (Agent DGI — région: Niamey)')
        self.stdout.write('  police@mycar.ne         / Admin1234!  (Police)')
        self.stdout.write('  contribuable@mycar.ne   / Admin1234!  (Contribuable — immat: NIA-001-A, tél: 0022790000001)')
        self.stdout.write('  distribution@mycar.ne   / Admin1234!  (Agent de distribution — région: Niamey)')

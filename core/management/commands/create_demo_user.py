from django.core.management.base import BaseCommand
from core.models import Utilisateur, RoleUtilisateur, Region


DEMO_USERS = [
    {
        'email':    'admin@mycar.ne',
        'password': 'Admin1234!',
        'role':     RoleUtilisateur.ADMIN_SYS,
        'nom':      'Admin',
        'prenom':   'Système',
        'region':   None,
    },
    {
        'email':    'superviseur@mycar.ne',
        'password': 'Admin1234!',
        'role':     RoleUtilisateur.SUP_DGI,
        'nom':      'Superviseur',
        'prenom':   'DGI',
        'region':   None,
    },
    {
        'email':    'agent@mycar.ne',
        'password': 'Admin1234!',
        'role':     RoleUtilisateur.AGENT_DGI,
        'nom':      'Agent',
        'prenom':   'DGI',
        'region':   'Niamey',
    },
    {
        'email':    'police@mycar.ne',
        'password': 'Admin1234!',
        'role':     RoleUtilisateur.POLICE,
        'nom':      'Officier',
        'prenom':   'Police',
        'region':   None,
    },
    {
        'email':    'distribution@mycar.ne',
        'password': 'Admin1234!',
        'role':     RoleUtilisateur.AGENT_DISTRIB,
        'nom':      'Agent',
        'prenom':   'Distribution',
        'region':   'Niamey',
    },
]


class Command(BaseCommand):
    help = 'Crée (ou recrée) les comptes de démonstration sans toucher aux données existantes'

    def handle(self, *args, **options):
        for u in DEMO_USERS:
            region = None
            if u['region']:
                region, _ = Region.objects.get_or_create(nom_region=u['region'])

            if Utilisateur.objects.filter(email=u['email']).exists():
                self.stdout.write(f"  [existe déjà] {u['email']}")
                continue

            Utilisateur.objects.create_user(
                email=u['email'],
                password=u['password'],
                role=u['role'],
                nom=u['nom'],
                prenom=u['prenom'],
                region=region,
            )
            self.stdout.write(self.style.SUCCESS(f"  [créé] {u['email']}"))

        self.stdout.write('\nComptes démo disponibles (mot de passe : Admin1234!) :')
        for u in DEMO_USERS:
            self.stdout.write(f"  {u['email']:<35} ({u['role']})")

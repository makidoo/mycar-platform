"""
Envoi des rappels SMS avant expiration des vignettes.

Logique :
  - Sélectionne les véhicules dont la vignette expire dans J+30, J+15 ou J+7
  - Envoie un SMS au propriétaire avec la date d'expiration et un lien
  - Evite les doublons : un seul SMS par véhicule par fenêtre (J+30 / J+15 / J+7)

Fréquence recommandée : quotidiennement à 08h00
  0 8 * * * cd /home/user/mycar-platform && docker compose -f docker-compose.local.yml exec -T web python manage.py rappels_expiration >> /var/log/mycar_rappels.log 2>&1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Automobile, StatutApprobationVehicule, StatutVignetteChoix
from core.sms_service import sms_rappel_expiration


FENETRES_JOURS = [30, 15, 7]


class Command(BaseCommand):
    help = 'Envoie des rappels SMS aux propriétaires dont la vignette expire bientôt'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simuler sans envoyer')
        parser.add_argument('--jours', type=int, default=None,
                            help='Forcer une fenêtre spécifique (ex: --jours 7)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fenetres = [options['jours']] if options['jours'] else FENETRES_JOURS
        aujourd_hui = timezone.now().date()

        self.stdout.write(
            f'[{timezone.now():%Y-%m-%d %H:%M}] Rappels expiration'
            f'{"  (DRY RUN)" if dry_run else ""}'
        )

        total_envoyes = 0

        for jours in fenetres:
            date_cible = aujourd_hui + timedelta(days=jours)

            autos = Automobile.objects.filter(
                statut_approbation=StatutApprobationVehicule.APPROUVE,
                statut_actuel__statut=StatutVignetteChoix.ORANGE,
                statut_actuel__date_fin_validite=date_cible,
            ).select_related('statut_actuel')

            self.stdout.write(
                f'  J+{jours} ({date_cible}) : {autos.count()} véhicule(s) à notifier'
            )

            for auto in autos:
                date_fin_str = date_cible.strftime('%d/%m/%Y')
                self.stdout.write(f'    → {auto.immatriculation} ({auto.telephone})')

                if not dry_run:
                    result = sms_rappel_expiration(auto.telephone, auto.immatriculation, date_fin_str)
                    if result['ok']:
                        total_envoyes += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'      ✗ Échec envoi SMS : {auto.immatriculation}')
                        )
                else:
                    total_envoyes += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nTerminé{"  (DRY RUN)" if dry_run else ""} — '
            f'{total_envoyes} SMS {"simulés" if dry_run else "envoyés"}'
        ))

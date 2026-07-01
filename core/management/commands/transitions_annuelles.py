"""
Transitions automatiques annuelles du cycle de vie des vignettes.

Règles (PDF §2 — Système de vignettes numériques) :
  VERT   → ORANGE
  ORANGE → ROUGE
  ROUGE  → ROUGE  (inchangé)

À exécuter le 1er janvier à 00h00 via cron :
  0 0 1 1 * python manage.py transitions_annuelles

Sur Ubuntu avec systemd-timer ou crontab :
  crontab -e
  0 0 1 1 * cd /home/user/mycar-platform && docker compose -f docker-compose.local.yml exec web python manage.py transitions_annuelles >> /var/log/mycar_transitions.log 2>&1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    Automobile, StatutVignette, StatutVignetteChoix,
    StatutApprobationVehicule, TypeModification, HistoriqueConsultation,
)


TRANSITIONS = {
    StatutVignetteChoix.VERT:   StatutVignetteChoix.ORANGE,
    StatutVignetteChoix.ORANGE: StatutVignetteChoix.ROUGE,
    StatutVignetteChoix.ROUGE:  None,  # inchangé
}


class Command(BaseCommand):
    help = 'Transitions automatiques annuelles VERT→ORANGE et ORANGE→ROUGE (1er janvier)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Simuler sans écrire en base',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Forcer l\'exécution même si la date n\'est pas le 1er janvier',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        dry_run = options['dry_run']
        force = options['force']

        if not force and (today.month != 1 or today.day != 1):
            self.stdout.write(self.style.WARNING(
                f'Aujourd\'hui ({today}) n\'est pas le 1er janvier. '
                f'Utilisez --force pour exécuter quand même.'
            ))
            return

        self.stdout.write(f'[{timezone.now()}] Début des transitions annuelles{"  (DRY RUN)" if dry_run else ""}')

        autos = Automobile.objects.filter(
            statut_approbation=StatutApprobationVehicule.APPROUVE,
            statut_actuel__isnull=False,
        ).select_related('statut_actuel')

        compteurs = {
            StatutVignetteChoix.VERT:   0,
            StatutVignetteChoix.ORANGE: 0,
            'ignore':                   0,
        }

        date_fin_annee = today.replace(month=12, day=31)

        for auto in autos:
            statut_courant = auto.statut_actuel.statut
            nouveau = TRANSITIONS.get(statut_courant)

            if nouveau is None:
                compteurs['ignore'] += 1
                continue

            if not dry_run:
                sv = StatutVignette.objects.create(
                    automobile=auto,
                    statut=nouveau,
                    date_debut_validite=today,
                    date_fin_validite=date_fin_annee,
                    type_modification=TypeModification.AUTO,
                    operateur=None,
                    notes_admin=f'Transition automatique annuelle {statut_courant} → {nouveau} — {today.year}',
                )
                auto.statut_actuel = sv
                auto.save(update_fields=['statut_actuel'])

                HistoriqueConsultation.objects.create(
                    utilisateur=None,
                    automobile=auto,
                    action_performee=f'Transition AUTO {statut_courant} → {nouveau}',
                    ip_address=None,
                )

            compteurs[statut_courant] += 1
            self.stdout.write(f'  {auto.immatriculation} : {statut_courant} → {nouveau}')

        self.stdout.write(self.style.SUCCESS(
            f'\nTerminé{"  (DRY RUN — aucune modification)" if dry_run else ""}\n'
            f'  VERT  → ORANGE : {compteurs[StatutVignetteChoix.VERT]}\n'
            f'  ORANGE → ROUGE : {compteurs[StatutVignetteChoix.ORANGE]}\n'
            f'  ROUGE (ignorés): {compteurs["ignore"]}'
        ))

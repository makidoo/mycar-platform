"""
Commande à lancer le 1er janvier de chaque année (cron : 0 0 1 1 *).

Règles :
  - VERT dont date_fin_validite < 1er janvier courant  → ORANGE
  - ORANGE dont date_fin_validite < 1er janvier de l'année précédente → ROUGE
    (= véhicule n'a pas renouvelé depuis 2 ans ou plus)
"""
from datetime import date
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    Automobile, StatutVignette, StatutVignetteChoix, TypeModification,
)


class Command(BaseCommand):
    help = 'Transition annuelle des statuts de vignettes (1er janvier)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simulation sans modification')
        parser.add_argument('--annee', type=int, default=None,
                            help='Année de référence (défaut : année courante)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        annee   = options['annee'] or timezone.now().year
        jan1_courant   = date(annee, 1, 1)
        jan1_precedent = date(annee - 1, 1, 1)

        self.stdout.write(f'Transition annuelle — référence : {jan1_courant}')
        if dry_run:
            self.stdout.write(self.style.WARNING('  [DRY-RUN] Aucune modification ne sera appliquée.'))

        # 1. VERT → ORANGE : vignettes valides l'an passé, pas encore renouvelées
        autos_vert = Automobile.objects.filter(
            statut_actuel__statut=StatutVignetteChoix.VERT,
            statut_actuel__date_fin_validite__lt=jan1_courant,
        ).select_related('statut_actuel')

        nb_vert = 0
        for auto in autos_vert:
            nb_vert += 1
            if not dry_run:
                sv = StatutVignette.objects.create(
                    automobile=auto,
                    statut=StatutVignetteChoix.ORANGE,
                    date_debut_validite=jan1_courant,
                    date_fin_validite=date(annee, 12, 31),
                    type_modification=TypeModification.AUTO,
                    operateur=None,
                    notes_admin=f'Transition automatique VERT→ORANGE au {jan1_courant} (vignette {auto.statut_actuel.date_fin_validite.year} expirée)',
                )
                auto.statut_actuel = sv
                auto.save(update_fields=['statut_actuel'])

        self.stdout.write(f'  VERT → ORANGE : {nb_vert} véhicule(s)')

        # 2. ORANGE → ROUGE : vignettes ORANGE depuis 2 ans ou plus
        autos_orange = Automobile.objects.filter(
            statut_actuel__statut=StatutVignetteChoix.ORANGE,
            statut_actuel__date_fin_validite__lt=jan1_precedent,
        ).select_related('statut_actuel')

        nb_orange = 0
        for auto in autos_orange:
            nb_orange += 1
            if not dry_run:
                sv = StatutVignette.objects.create(
                    automobile=auto,
                    statut=StatutVignetteChoix.ROUGE,
                    date_debut_validite=jan1_courant,
                    date_fin_validite=date(annee, 12, 31),
                    type_modification=TypeModification.AUTO,
                    operateur=None,
                    notes_admin=f'Transition automatique ORANGE→ROUGE au {jan1_courant} (non renouvelé depuis {auto.statut_actuel.date_fin_validite.year})',
                )
                auto.statut_actuel = sv
                auto.save(update_fields=['statut_actuel'])

        self.stdout.write(f'  ORANGE → ROUGE : {nb_orange} véhicule(s)')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Transition terminée : {nb_vert + nb_orange} véhicule(s) mis à jour.'))
        else:
            self.stdout.write(f'[DRY-RUN] {nb_vert + nb_orange} véhicule(s) auraient été mis à jour.')

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_journalaudit'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionSpeciale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50, choices=[
                    ('APPROUVER_VEHICULE', 'Approuver / Rejeter des véhicules'),
                    ('TRAITER_TRANSFERT',  'Traiter les transferts de propriété'),
                    ('ATTRIBUER_VIGNETTE', 'Attribuer les vignettes physiques'),
                    ('PAIEMENT_AGENCE',    'Effectuer des paiements en agence'),
                    ('TRAITER_PLAINTES',   'Traiter les plaintes & litiges'),
                    ('VOIR_RAPPORTS',      'Accéder aux rapports'),
                    ('VOIR_JOURNAL_AUDIT', "Consulter le journal d'audit"),
                    ('GERER_UTILISATEURS', 'Gérer les comptes utilisateurs'),
                ])),
                ('date_accord', models.DateTimeField(auto_now_add=True)),
                ('accordee_par', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='permissions_accordees',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('utilisateur', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permissions_speciales',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'unique_together': {('utilisateur', 'action')}},
        ),
    ]

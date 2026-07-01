import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_approbation_statut_physique'),
    ]

    operations = [
        # Nouveau rôle AGENT_DISTRIBUTION dans les choices
        migrations.AlterField(
            model_name='utilisateur',
            name='role',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('ADMINISTRATEUR_SYSTEME', 'Administrateur Système'),
                    ('SUPERVISEUR_DGI',        'Superviseur DGI'),
                    ('AGENT_DGI',              'Agent DGI'),
                    ('AGENT_DISTRIBUTION',     'Agent de distribution'),
                    ('POLICE',                 'Police'),
                    ('CONTRIBUABLE',           'Contribuable'),
                ],
            ),
        ),
        # Modèle DemandeTransfert
        migrations.CreateModel(
            name='DemandeTransfert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ancien_nom',        models.CharField(max_length=100)),
                ('ancien_prenom',     models.CharField(max_length=100)),
                ('ancien_telephone',  models.CharField(max_length=20)),
                ('nouveau_nom',       models.CharField(max_length=100)),
                ('nouveau_prenom',    models.CharField(max_length=100)),
                ('nouveau_telephone', models.CharField(max_length=20)),
                ('motif',             models.TextField(blank=True)),
                ('statut', models.CharField(
                    max_length=20,
                    choices=[('EN_ATTENTE', 'En attente'), ('APPROUVE', 'Approuvé'), ('REJETE', 'Rejeté')],
                    default='EN_ATTENTE',
                )),
                ('notes_admin',       models.TextField(blank=True)),
                ('date_demande',      models.DateTimeField(auto_now_add=True)),
                ('date_traitement',   models.DateTimeField(null=True, blank=True)),
                ('automobile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transferts', to='core.automobile')),
                ('traite_par', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transferts_traites',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]

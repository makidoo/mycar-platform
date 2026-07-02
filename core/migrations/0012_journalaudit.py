from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_duree_annees_paiement'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('utilisateur_email', models.CharField(blank=True, max_length=255)),
                ('utilisateur_role',  models.CharField(blank=True, max_length=50)),
                ('categorie',         models.CharField(max_length=20, choices=[
                    ('CONNEXION','Connexion'), ('VEHICULE','Véhicule'), ('PAIEMENT','Paiement'),
                    ('UTILISATEUR','Utilisateur'), ('DISTRIBUTION','Distribution'),
                    ('TRANSFERT','Transfert'), ('PARAMETRES','Paramètres'), ('POLICE','Police'),
                ])),
                ('action',      models.CharField(max_length=200)),
                ('detail',      models.TextField(blank=True)),
                ('objet_type',  models.CharField(blank=True, max_length=50)),
                ('objet_id',    models.CharField(blank=True, max_length=50)),
                ('objet_label', models.CharField(blank=True, max_length=200)),
                ('ip_address',  models.GenericIPAddressField(blank=True, null=True)),
                ('date_action', models.DateTimeField(auto_now_add=True)),
                ('utilisateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='journal',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-date_action']},
        ),
    ]

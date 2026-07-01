import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_agent_distribution_transfert'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('canal',        models.CharField(max_length=10,  default='SMS')),
                ('destinataire', models.CharField(max_length=50)),
                ('message',      models.TextField()),
                ('contexte',     models.CharField(max_length=100, blank=True)),
                ('statut',       models.CharField(max_length=20,  default='MOCK')),
                ('date_envoi',   models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Plainte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference',       models.CharField(max_length=20,  unique=True, blank=True)),
                ('nom_plaignant',   models.CharField(max_length=100)),
                ('telephone',       models.CharField(max_length=20)),
                ('sujet',           models.CharField(max_length=200)),
                ('description',     models.TextField()),
                ('statut', models.CharField(
                    max_length=20,
                    choices=[
                        ('OUVERTE',  'Ouverte'),
                        ('EN_COURS', 'En cours de traitement'),
                        ('RESOLUE',  'Résolue'),
                        ('REJETEE',  'Rejetée'),
                    ],
                    default='OUVERTE',
                )),
                ('reponse_admin',   models.TextField(blank=True)),
                ('date_creation',   models.DateTimeField(auto_now_add=True)),
                ('date_traitement', models.DateTimeField(null=True, blank=True)),
                ('automobile', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='plaintes',
                    to='core.automobile',
                )),
                ('traite_par', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='plaintes_traitees',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]

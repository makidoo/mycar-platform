from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_paiement_operateur'),
    ]

    operations = [
        # Automobile : workflow d'approbation + année fabrication
        migrations.AddField(
            model_name='automobile',
            name='statut_approbation',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('EN_ATTENTE', 'En attente'),
                    ('APPROUVE',   'Approuvé'),
                    ('REJETE',     'Rejeté'),
                    ('SUSPENDU',   'Suspendu'),
                ],
                default='EN_ATTENTE',
            ),
        ),
        migrations.AddField(
            model_name='automobile',
            name='notes_approbation',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='automobile',
            name='annee_fabrication',
            field=models.IntegerField(null=True, blank=True),
        ),
        # TypeVehicule : bus + camion
        migrations.AlterField(
            model_name='automobile',
            name='type_vehicule',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('VEHICULE', 'Véhicule'),
                    ('MOTO',     'Moto'),
                    ('BUS',      'Bus'),
                    ('CAMION',   'Camion'),
                ],
            ),
        ),
        # StatutVignette : suivi physique + champs audit manuels
        migrations.AddField(
            model_name='statutvignette',
            name='statut_physique',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('NON_ATTRIBUE', 'Non attribué'),
                    ('ATTRIBUE',     'Attribué'),
                ],
                default='NON_ATTRIBUE',
            ),
        ),
        migrations.AddField(
            model_name='statutvignette',
            name='numero_recu',
            field=models.CharField(max_length=100, blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='statutvignette',
            name='notes_admin',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]

from django.db import migrations

FORMAT_IMMAT_DEFAUT = r'[A-Z]{2}[0-9]{4}[A-Z]{2,5}'
FORMAT_IMMAT_DESCRIPTION = "Regex de validation du format de plaque (ex: AB1234NIA)"


def creer_parametre_format_immat(apps, schema_editor):
    ParametrePlateforme = apps.get_model('core', 'ParametrePlateforme')
    ParametrePlateforme.objects.get_or_create(
        cle='format_immatriculation',
        defaults={'valeur': FORMAT_IMMAT_DEFAUT, 'description': FORMAT_IMMAT_DESCRIPTION},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_region_code_format_immat'),
    ]

    operations = [
        migrations.RunPython(creer_parametre_format_immat, migrations.RunPython.noop),
    ]

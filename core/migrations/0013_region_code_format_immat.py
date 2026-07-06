from django.db import migrations, models

CODES_REGIONS = {
    'Niamey':     'NIA',
    'Zinder':     'ZIN',
    'Maradi':     'MAR',
    'Tahoua':     'TAH',
    'Agadez':     'AGA',
    'Dosso':      'DOS',
    'Tillabéri':  'TIL',
    'Diffa':      'DIF',
}


def populate_codes_region(apps, schema_editor):
    Region = apps.get_model('core', 'Region')
    for region in Region.objects.all():
        region.code_region = CODES_REGIONS.get(region.nom_region, region.nom_region[:3].upper())
        region.save(update_fields=['code_region'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_journalaudit'),
    ]

    operations = [
        migrations.AddField(
            model_name='region',
            name='code_region',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.RunPython(populate_codes_region, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='region',
            name='code_region',
            field=models.CharField(blank=True, default='', max_length=5, unique=True),
        ),
    ]

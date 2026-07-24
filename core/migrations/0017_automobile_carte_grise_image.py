from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_alter_automobile_options_alter_region_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='automobile',
            name='carte_grise_image',
            field=models.ImageField(blank=True, null=True, upload_to='cartes_grises/'),
        ),
    ]

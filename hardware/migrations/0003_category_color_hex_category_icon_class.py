"""
Migration to add color_hex and icon_class to Category.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware', '0002_restructure_and_logging'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='color_hex',
            field=models.CharField(blank=True, max_length=7),
        ),
        migrations.AddField(
            model_name='category',
            name='icon_class',
            field=models.CharField(blank=True, max_length=120),
        ),
    ]

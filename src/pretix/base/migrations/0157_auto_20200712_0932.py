# Generated by Django 3.0.6 on 2020-07-12 09:32

from django.db import migrations, models

import pretix.helpers.countries


class Migration(migrations.Migration):

    dependencies = [
        ('pretixbase', '0156_cartposition_override_tax_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemaddon',
            name='multi_allowed',
            field=models.BooleanField(default=False),
        ),
    ]
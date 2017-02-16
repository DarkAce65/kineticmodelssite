# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-23 10:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kineticmodels', '0038_auto_20160623_1033'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Comment',
            new_name='KineticsComment',
        ),
        migrations.AlterField(
            model_name='kineticmodel',
            name='kinetics',
            field=models.ManyToManyField(through='kineticmodels.KineticsComment', to='kineticmodels.Kinetics'),
        ),
    ]

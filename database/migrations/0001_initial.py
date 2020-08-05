# Generated by Django 3.0.3 on 2020-08-05 02:35

import database.models.kinetic_model
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstname', models.CharField(max_length=80)),
                ('lastname', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='Authorship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(verbose_name='Order of authorship')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Author')),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='BaseKineticsData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.FloatField(blank=True, help_text='Overall reaction order', null=True)),
                ('min_temp', models.FloatField(blank=True, help_text='units: K', null=True, verbose_name='Lower Temp Bound')),
                ('max_temp', models.FloatField(blank=True, help_text='units: K', null=True, verbose_name='Upper Temp Bound')),
                ('min_pressure', models.FloatField(blank=True, help_text='units: Pa', null=True, verbose_name='Lower Pressure Bound')),
                ('max_pressure', models.FloatField(blank=True, help_text='units: Pa', null=True, verbose_name='Upper Pressure Bound')),
            ],
        ),
        migrations.CreateModel(
            name='Isomer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inchi', models.CharField(blank=True, max_length=500, verbose_name='InChI')),
            ],
        ),
        migrations.CreateModel(
            name='KineticModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.CharField(max_length=200, unique=True)),
                ('prime_id', models.CharField(blank=True, max_length=9, verbose_name='PrIMe ID')),
                ('info', models.CharField(blank=True, max_length=1000)),
                ('chemkin_reactions_file', models.FileField(blank=True, upload_to=database.models.kinetic_model.upload_chemkin_to)),
                ('chemkin_thermo_file', models.FileField(blank=True, upload_to=database.models.kinetic_model.upload_thermo_to)),
                ('chemkin_transport_file', models.FileField(blank=True, upload_to=database.models.kinetic_model.upload_transport_to)),
            ],
            options={
                'verbose_name_plural': 'Kinetic Models',
            },
        ),
        migrations.CreateModel(
            name='Kinetics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prime_id', models.CharField(blank=True, max_length=10)),
                ('relative_uncertainty', models.FloatField(blank=True, null=True)),
                ('reverse', models.BooleanField(default=False, help_text='Is this the rate for the reverse reaction?')),
                ('base_data', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='database.BaseKineticsData')),
            ],
            options={
                'verbose_name_plural': 'Kinetics',
            },
        ),
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prime_id', models.CharField(blank=True, max_length=10, verbose_name='PrIMe ID')),
                ('reversible', models.BooleanField()),
            ],
            options={
                'ordering': ('prime_id',),
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doi', models.CharField(blank=True, max_length=80)),
                ('prime_id', models.CharField(blank=True, max_length=9, verbose_name='Prime ID')),
                ('publication_year', models.CharField(blank=True, max_length=4, verbose_name='Year of Publication')),
                ('source_title', models.CharField(blank=True, max_length=300, verbose_name='Article Title')),
                ('journal_name', models.CharField(blank=True, max_length=300, verbose_name='Journal Name')),
                ('journal_volume_number', models.CharField(blank=True, max_length=10, verbose_name='Journal Volume Number')),
                ('page_numbers', models.CharField(blank=True, help_text='[page #]-[page #]', max_length=100, verbose_name='Page Numbers')),
                ('authors', models.ManyToManyField(blank=True, through='database.Authorship', to='database.Author')),
            ],
            options={
                'ordering': ('prime_id',),
            },
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prime_id', models.CharField(blank=True, max_length=9, verbose_name='PrIMe ID')),
                ('formula', models.CharField(max_length=50)),
                ('inchi', models.CharField(blank=True, max_length=500, verbose_name='InChI')),
                ('cas_number', models.CharField(blank=True, max_length=400, verbose_name='CAS Registry Number')),
            ],
            options={
                'verbose_name_plural': 'Species',
                'ordering': ('prime_id',),
            },
        ),
        migrations.CreateModel(
            name='Thermo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prime_id', models.CharField(blank=True, max_length=11)),
                ('preferred_key', models.CharField(blank=True, help_text='i.e. T 11/97, or J 3/65', max_length=20)),
                ('reference_temp', models.FloatField(default=0.0, help_text='units: K', verbose_name='Reference State Temperature')),
                ('reference_pressure', models.FloatField(default=0.0, help_text='units: Pa', verbose_name='Reference State Pressure')),
                ('enthalpy_formation', models.FloatField(help_text='units: J/mol', null=True, verbose_name='Enthalpy of Formation')),
                ('coeffs_poly1', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=7)),
                ('coeffs_poly2', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=7)),
                ('temp_min_1', models.FloatField(help_text='units: K', verbose_name='Polynomial 1 Lower Temp Bound')),
                ('temp_max_1', models.FloatField(help_text='units: K', verbose_name='Polynomial 1 Upper Temp Bound')),
                ('temp_min_2', models.FloatField(help_text='units: K', verbose_name='Polynomial 2 Lower Temp Bound')),
                ('temp_max_2', models.FloatField(help_text='units: K', verbose_name='Polynomial 2 Upper Temp Bound')),
                ('source', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='database.Source')),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Species')),
            ],
        ),
        migrations.CreateModel(
            name='Transport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prime_id', models.CharField(blank=True, max_length=10)),
                ('geometry', models.FloatField(blank=True, default=0.0)),
                ('potential_well_depth', models.FloatField(blank=True, default=0.0, help_text='units: K', verbose_name='Potential Well Depth')),
                ('collision_diameter', models.FloatField(blank=True, default=0.0, help_text='units: angstroms', verbose_name='Collision Diameter')),
                ('dipole_moment', models.FloatField(blank=True, default=0.0, help_text='units: debye')),
                ('polarizability', models.FloatField(blank=True, default=0.0, help_text='units: cubic angstroms')),
                ('rotational_relaxation', models.FloatField(blank=True, default=0.0, verbose_name='Rotational Relaxation')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Source')),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Species')),
            ],
        ),
        migrations.CreateModel(
            name='Arrhenius',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('a_value', models.FloatField(default=0.0)),
                ('a_value_uncertainty', models.FloatField(blank=True, null=True)),
                ('n_value', models.FloatField(default=0.0)),
                ('e_value', models.FloatField(default=0.0)),
                ('e_value_uncertainty', models.FloatField(blank=True, null=True)),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='ArrheniusEP',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('a', models.FloatField()),
                ('n', models.FloatField()),
                ('ep_alpha', models.FloatField()),
                ('e0', models.FloatField()),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='Chebyshev',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('coefficient_matrix', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=None), blank=True, null=True, size=None)),
                ('units', models.CharField(max_length=25)),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='KineticsData',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('temp_array', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=None)),
                ('rate_coefficients', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=None)),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='PDepArrhenius',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='TransportComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(blank=True, max_length=1000)),
                ('kinetic_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.KineticModel')),
                ('transport', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Transport')),
            ],
        ),
        migrations.CreateModel(
            name='ThermoComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True)),
                ('kinetic_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.KineticModel')),
                ('thermo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Thermo')),
            ],
        ),
        migrations.CreateModel(
            name='Structure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('smiles', models.CharField(blank=True, max_length=500, verbose_name='SMILES')),
                ('adjacency_list', models.TextField(unique=True, verbose_name='Adjacency List')),
                ('multiplicity', models.IntegerField()),
                ('isomer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Isomer')),
            ],
        ),
        migrations.CreateModel(
            name='Stoichiometry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stoichiometry', models.FloatField()),
                ('reaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Reaction')),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Species')),
            ],
            options={
                'verbose_name_plural': 'Stoichiometries',
                'unique_together': {('species', 'reaction', 'stoichiometry')},
            },
        ),
        migrations.CreateModel(
            name='SpeciesName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200)),
                ('kinetic_model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='database.KineticModel')),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Species')),
            ],
            options={
                'verbose_name_plural': 'Alternative Species Names',
            },
        ),
        migrations.AddField(
            model_name='reaction',
            name='species',
            field=models.ManyToManyField(through='database.Stoichiometry', to='database.Species'),
        ),
        migrations.CreateModel(
            name='KineticsComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(blank=True, max_length=1000)),
                ('kinetic_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.KineticModel')),
                ('kinetics', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Kinetics')),
            ],
        ),
        migrations.AddField(
            model_name='kinetics',
            name='reaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Reaction'),
        ),
        migrations.AddField(
            model_name='kinetics',
            name='source',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='database.Source'),
        ),
        migrations.AddField(
            model_name='kineticmodel',
            name='kinetics',
            field=models.ManyToManyField(through='database.KineticsComment', to='database.Kinetics'),
        ),
        migrations.AddField(
            model_name='kineticmodel',
            name='source',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='database.Source'),
        ),
        migrations.AddField(
            model_name='kineticmodel',
            name='species',
            field=models.ManyToManyField(through='database.SpeciesName', to='database.Species'),
        ),
        migrations.AddField(
            model_name='kineticmodel',
            name='thermo',
            field=models.ManyToManyField(through='database.ThermoComment', to='database.Thermo'),
        ),
        migrations.AddField(
            model_name='kineticmodel',
            name='transport',
            field=models.ManyToManyField(through='database.TransportComment', to='database.Transport'),
        ),
        migrations.AddField(
            model_name='isomer',
            name='species',
            field=models.ManyToManyField(to='database.Species'),
        ),
        migrations.CreateModel(
            name='Efficiency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('efficiency', models.FloatField()),
                ('kinetics_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.BaseKineticsData')),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Species')),
            ],
        ),
        migrations.AddField(
            model_name='basekineticsdata',
            name='collider_efficiencies',
            field=models.ManyToManyField(blank=True, through='database.Efficiency', to='database.Species'),
        ),
        migrations.AddField(
            model_name='authorship',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Source'),
        ),
        migrations.CreateModel(
            name='Troe',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('alpha', models.FloatField()),
                ('t1', models.FloatField()),
                ('t2', models.FloatField(blank=True, default=0.0)),
                ('t3', models.FloatField()),
                ('high_arrhenius', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='database.Arrhenius')),
                ('low_arrhenius', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='database.Arrhenius')),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='ThirdBody',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('low_arrhenius', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='database.Arrhenius')),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='Pressure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pressure', models.FloatField()),
                ('arrhenius', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='database.Arrhenius')),
                ('pdep_arrhenius', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.PDepArrhenius')),
            ],
        ),
        migrations.AddField(
            model_name='pdeparrhenius',
            name='arrhenius_set',
            field=models.ManyToManyField(through='database.Pressure', to='database.Arrhenius'),
        ),
        migrations.CreateModel(
            name='MultiPDepArrhenius',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('pdep_arrhenius_set', models.ManyToManyField(to='database.PDepArrhenius')),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='MultiArrhenius',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('arrhenius_set', models.ManyToManyField(to='database.Arrhenius')),
            ],
            bases=('database.basekineticsdata',),
        ),
        migrations.CreateModel(
            name='Lindemann',
            fields=[
                ('basekineticsdata_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.BaseKineticsData')),
                ('high_arrhenius', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='database.Arrhenius')),
                ('low_arrhenius', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='database.Arrhenius')),
            ],
            bases=('database.basekineticsdata',),
        ),
    ]
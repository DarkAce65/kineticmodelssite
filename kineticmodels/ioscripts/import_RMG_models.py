#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Import the contents of the RMG-models repository.

Run this like so:
 $  python import_RMG_models.py /path/to/local/RMG-models/
 
It should dig through all the models and import them into
the Django database.
"""

# Not Django-specific imports
import sys
import os
import time
import re
import argparse
import logging
import abc
import datetime

# Django setup to import models and other files from the Apps
sys.path.append('../..')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rmgweb.settings")
import django
django.setup()

# Django-specific imports
from django.core.exceptions import MultipleObjectsReturned
from kineticmodels.models import Kinetics, ArrheniusKinetics, Reaction, Stoichiometry, \
    Species, KineticModel, SpeciesName, \
    Thermo, ThermoComment, Structure, Isomer, \
    Source, Author, Authorship, Transport

import rmgpy
from rmgpy.thermo import NASA, ThermoData, Wilhoit, NASAPolynomial
import rmgpy.constants as constants
from rmgpy.kinetics import Arrhenius, ArrheniusEP, ThirdBody, Lindemann, Troe, \
                           PDepArrhenius, MultiArrhenius, MultiPDepArrhenius, \
                           Chebyshev, KineticsData, PDepKineticsModel
from rmgpy.data.kinetics.library import KineticsLibrary
from rmgpy.data.thermo import ThermoLibrary
from __builtin__ import True


class ImportError(Exception):
    pass


class Importer(object):
    """
    Abstraction of the Importer Classes for Kinetics and Thermo data, each found below
    Note that all of these methods must be overridden when this class is inherited
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, path):
        self.path = path
        self.name = self.name_from_path(path)
        self.library = None

    @abc.abstractmethod
    def name_from_path(self, path=None):
        """
        Get the library name from the (full) path
        """
        name_path_re = re.compile('\.*\/?(.+?)\/RMG-Py-.*-library.*')
        match = name_path_re.match(path or self.path)
        if match:
            return match.group(1).split('RMG-models/')[-1]
        else:
            return os.path.split(self.path)[0]

    @abc.abstractmethod
    def load_library(self):
        """
        Load from file. This method should be overridden in subclasses of this Importer class.
        """
        raise NotImplementedError("Should define this in a subclass")

    @abc.abstractmethod
    def import_data(self):
        """
        Import the data to django. This method should be overridden in subclasses of this Importer class.
        """
        raise NotImplementedError("Should define this in a subclass")


class ThermoLibraryImporter(Importer):
    """
    To import a thermodynamic library
    """

    def __init__(self, path):
        return super(ThermoLibraryImporter, self).__init__(path=path)

    def name_from_path(self, path=None):
        return super(ThermoLibraryImporter, self).name_from_path(path=path)

    def load_library(self):
        """
        Load the thermo library from the path, and store it.
        """
        filename = self.path
        # Define local context to allow for loading of the library
        local_context = {
                'ThermoData': ThermoData,
                'Wilhoit': Wilhoit,
                'NASAPolynomial': NASAPolynomial,
                'NASA': NASA,
            }

        # Load the library
        library = ThermoLibrary(label=self.name)
        library.SKIP_DUPLICATES = True
        # NOTE -- In order for this feature to run we have to be on "rmg-py/importer" branch, may require reinstall
        library.load(filename, local_context=local_context)
        self.library = library

    def import_species(self):
        """
        Import the Species only, not their thermo
        """
        library = self.library
        for entry in library.entries:
            thermo = library.entries[entry].data
            molecule = library.entries[entry].item
            speciesName = library.entries[entry].label

            smiles = molecule.toSMILES()
            inchi = molecule.toInChI()
            # Search for Structure matching the SMILES
            dj_structure, structure_created = Structure.objects.get_or_create(smiles=smiles,
                                                                              electronicState=molecule.multiplicity)
            if structure_created:
                dj_structure.adjacencyList = molecule.toAdjacencyList()
                # save it once you've added the Isomer (required)
                dj_isomer = Isomer.objects.create(inchi=inchi)
                dj_structure.isomer = dj_isomer
                dj_structure.save()
            else:
                assert dj_structure.adjacencyList == molecule.toAdjacencyList(), \
                    "{}\n is not\n{}\n{}\nwhich had SMILES={!r}".format(dj_structure.adjacencyList,
                                                                        speciesName, molecule.toAdjacencyList(), smiles)
                dj_isomer = dj_structure.isomer  # might there be more than one? (no?)

            # Find a Species for the Structure (eg. from Prime) else make one
            trimmed_inchi = inchi.split('InChI=1S')[-1]
            formula = inchi.split('/')[1]
            try:
                dj_species, species_created = Species.objects.get_or_create(inchi__contains=trimmed_inchi)
                if species_created:
                    logger.debug("Found no species for structure {} {}, so making one".format(smiles,
                                                                                              molecule.multiplicity))
                    dj_species.inchi = inchi
                    dj_species.formula = formula
                    dj_species.save()
                    logger.debug("{}".format(dj_species))
                else:
                    logger.debug("Found a unique species {} for structure {} {}".format(dj_species, smiles,
                                                                                        molecule.multiplicity))
                    dj_isomer.species.add(dj_species)

            except MultipleObjectsReturned:
                possible_species = Species.objects.filter(inchi__contains=trimmed_inchi)
                logger.warning("ThermoLibraryImporter.import_species: Found {} species for structure {} {}!".format(
                    len(possible_species), smiles, molecule.multiplicity))
                logger.warning(possible_species)
                dj_species = None  # TODO: how do we pick one?

            # If we got a unique match for the Species, find a Kinetic Model for that Species else make one
            if dj_species:
                # Create a Kinetic Model
                dj_km, km_created = KineticModel.objects.get_or_create(rmgImportPath=self.name)
                if km_created:
                    dj_km.modelName = self.name
                    dj_km.additionalInfo = "Created while importing RMG-models"
                    # Save that instance
                    try:
                        dj_km.save()
                        logger.info("Created the following Kinetic Model Instance:\n{0}\n".format(dj_km))
                    except Exception, e:
                        logger.error("Error saving the Kinetic Model: {}".format(e))
                        raise e

                # Create the join between Species and KineticModel through a SpeciesName
                dj_speciesName, species_name_created = SpeciesName.objects.get_or_create(species=dj_species,
                                                                                         kineticModel=dj_km)
                dj_speciesName.name = speciesName
                dj_speciesName.save()

                # Save the pk of the django Species instances to the Entry so we can lookup add the thermo later
                library.entries[entry].dj_species_pk = dj_species.pk

        # And then save the new library that contains all the entries updated with Species instances
        self.library = library

    def import_data(self):
        """
        Import the loaded thermo library into the django database
        Unpacks the coefficients from the NASAPolynomials and stores them in a Thermo
        """
        library = self.library
        for entry in library.entries:
            thermoEntry = library.entries[entry].data
            chemkinMolecule = library.entries[entry].item
            name = library.entries[entry].label
            species_pk = library.entries[entry].dj_species_pk

            dj_thermo = Thermo()  # Empty Thermo model instance from Django kineticmodelssite
            # TODO -- Is it necessary/possible to do a get_or_create here? If so, what's the identifying info?

            """
            We're given a list of NASAPolynomial objects, each of which needs to be unpacked into its coefficients
            In the Thermo model instance we're creating, we name the coefficients "coefficient41":
                - where the first number is the coefficient number (ranges from 1 to 7)
                - and the second number is the polynomial number (either #1 or #2)
            To set these attributes, we need to access both the index and the value of the items we're iterating over
            Normally we would be forced to choose between "for i in list" and "for i in range(len(list))"
            However, enumerate() lets us iterate over a list of tuples, each of which contains the index and the item itself
            We even get to set a +1 offset for the indices when making these tuples to avoid naming errors
            """
            for nasaPolynomial in list(enumerate(thermoEntry.polynomials, start=1)):  # <-- List of tuples (index, Poly)
                # To refer to a polynomial's index is nasaPolynomial[0], and the polynomial itself is nasaPolynomial[1]

                # Assign lower Temp Bound for Polynomial and log success
                try:
                    setattr(dj_thermo,
                            "lowerTempBound{}".format(nasaPolynomial[0]),
                            nasaPolynomial[1].Tmin)
                    logger.debug("Assigned value {1} to lowerTempBound{0}".format(nasaPolynomial[0],
                                                                                  nasaPolynomial[1].Tmin))
                except Exception, e:
                    logger.error("Error assigning the lower temperature bound to "
                                 "Polynomial {1}:\n{0}\n".format(e,
                                                                 nasaPolynomial[0]))
                    raise e

                # Assign upper Temp Bound for Polynomial and log success
                try:
                    setattr(dj_thermo,
                            "upperTempBound{}".format(nasaPolynomial[0]),
                            nasaPolynomial[1].Tmax)
                    logger.debug("Assigned value {1} to upperTempBound{0}".format(nasaPolynomial[0],
                                                                                  nasaPolynomial[1].Tmax))
                except Exception, e:
                    logger.error("Error assigning the upper temperature bound to "
                                 "Polynomial {1}:\n{0}\n".format(e,
                                                                 nasaPolynomial[0]))
                    raise e

                # Assign coefficients for Polynomial and log success
                for coefficient in list(enumerate(nasaPolynomial[1].coeffs, start=1)):  # <-- List of tuples (index, coeff)
                    # Once again, a coefficent's index is coefficient[0], and its value is coefficient[1]
                    try:
                        setattr(dj_thermo,
                                "coefficient{1}{0}".format(nasaPolynomial[0], coefficient[0]),
                                coefficient[1])
                        logger.debug("Assigned value {2} for coefficient {1}"
                                     " to Polynomial {0}".format(nasaPolynomial[0],
                                                                 coefficient[0],
                                                                 coefficient[1]))
                    except Exception, e:
                        logger.error("Error assigning the value {3} to coefficient {2} of "
                                     "Polynomial {1}:\n{0}\n".format(e,
                                                                     nasaPolynomial[0],
                                                                     coefficient[0],
                                                                     coefficient[1]))
                        raise e

            # Tie the thermo data to a species using the Species primary key saved in the Entry from import_species
            if species_pk:
                dj_thermo.species = Species.objects.get(pk=species_pk)


            # TODO -- We're still missing the Thermo's Source link as well as its ThermoComment link to a KineticModel

            # Save the thermo data
            try:
                dj_thermo.save()
                logger.info("Created the following Thermo Data Instance:\n{}\n".format(dj_thermo))
            except Exception, e:
                logger.error("Error saving the Thermo data:\n{}\n".format(e))
                raise e


class KineticsLibraryImporter(Importer):
    """
    To import a kinetics library
    """

    def __init__(self, path):
        return super(KineticsLibraryImporter, self).__init__(path=path)

    def name_from_path(self, path=None):
        return super(KineticsLibraryImporter, self).name_from_path(path=path)

    def load_library(self):
        """
        Load the kinetics library from the path and store it
        """
        fileName = self.path
        # Define local context to allow for loading of the library
        local_context = {
                    'KineticsData': KineticsData,
                    'Arrhenius': Arrhenius,
                    'ArrheniusEP': ArrheniusEP,
                    'MultiArrhenius': MultiArrhenius,
                    'MultiPDepArrhenius': MultiPDepArrhenius,
                    'PDepArrhenius': PDepArrhenius,
                    'Chebyshev': Chebyshev,
                    'ThirdBody': ThirdBody,
                    'Lindemann': Lindemann,
                    'Troe': Troe,
                    'R': constants.R,
                }
        # Load the library
        logger.info("Loading reaction library {0}".format(fileName))
        library = KineticsLibrary(label=self.name)
        library.ALLOW_UNMARKED_DUPLICATES = True
        try:
            library.load(fileName, local_context=local_context)
        except Exception, e:
            logger.error("Error reading {0}:".format(fileName), exc_info=True)
            logger.warning("Will continue without that model")
            return False

        library.convertDuplicatesToMulti()
        self.library = library

    def import_data(self):
        """
        Import the loaded kinetics library into the django database
        """
        library = self.library
        for entry in library.entries:
            kinetics = library.entries[entry].data
            chemkinReaction = library.entries[entry].item
            #TODO: make this do something

"""
class PrimeSpeciesImporter(Importer):

    To import chemical species. Left over from PrIMe importer


    def import_elementtree_root(self, species):
        ns = self.ns
        primeID = species.attrib.get("primeID")
        dj_item, created = Species.objects.get_or_create(sPrimeID=primeID)
        identifier = species.find('prime:chemicalIdentifier', namespaces=ns)
        for name in identifier.findall('prime:name', namespaces=ns):
            if 'type' in name.attrib:
                if name.attrib['type'] == 'formula':
                    dj_item.formula = name.text
                elif name.attrib['type'] == 'CASRegistryNumber':
                    dj_item.CAS = name.text
                elif name.attrib['type'] == 'InChI':
                    dj_item.inchi = name.text
            else:
                # it's just a random name
                if not name.text:
                    logger.warning("Blank species name in species {}".format(primeID))
                    continue
                SpeciesName.objects.get_or_create(species=dj_item, name=name.text)
        dj_item.save()
        # import ipdb; ipdb.set_trace()


class PrimeThermoImporter(Importer):

    To import the thermodynamic data of a species (can be multiple for each species). Left over from PrIMe importer

    prime_ID_prefix = 'thp'

    def import_elementtree_root(self, thermo):
        ns = self.ns
        # Get the Prime ID for the thermo polynomial
        if thermo.attrib.get("primeID") != 'thp00000000':
            thpPrimeID = thermo.attrib.get("primeID")
        else:
            return
        # Get the Prime ID for the species to which it belongs, and get (or create) the species
        specieslink = thermo.find('prime:speciesLink', namespaces=ns)
        sPrimeID = specieslink.attrib['primeID']
        species, created = Species.objects.get_or_create(sPrimeID=sPrimeID)
        # Now get (or create) the django Thermo object for that species and polynomial
        dj_thermo, created = Thermo.objects.get_or_create(
            thpPrimeID=thpPrimeID,
            species=species)

        # Start by finding the source link, and looking it up in the bibliography
        bibliography_link = thermo.find('prime:bibliographyLink',
                                        namespaces=ns)
        bPrimeID = bibliography_link.attrib['primeID']
        source, created = Source.objects.get_or_create(bPrimeID=bPrimeID)
        dj_thermo.source = source

        # Now give the Thermo object its other properties
        dj_thermo.preferred_key = thermo.findtext('prime:preferredKey',
                                                  namespaces=ns,
                                                  default='')

        dfH = thermo.find('prime:dfH', namespaces=ns)
        if dfH is not None and dfH.text.strip():
            dj_thermo.dfH = float(dfH.text)
        reference = thermo.find('prime:referenceState', namespaces=ns)
        Tref = reference.find('prime:Tref', namespaces=ns)
        if Tref is not None:
            dj_thermo.reference_temperature = float(Tref.text)
        Pref = reference.find('prime:Pref', namespaces=ns)
        if Pref is not None:
            dj_thermo.reference_pressure = float(Pref.text)
        for i, polynomial in enumerate(thermo.findall('prime:polynomial',
                                                      namespaces=ns)):
            polynomial_number = i + 1
            for j, coefficient in enumerate(polynomial.findall('prime:coefficient', namespaces=ns)):
                coefficient_number = j + 1
                assert coefficient_number == int(coefficient.attrib['id'])
                value = float(coefficient.text)
                # Equivalent of: dj_item.coefficient_1_1 = value
                setattr(dj_thermo,
                        'coefficient_{0}_{1}'.format(coefficient_number, polynomial_number),
                        value)
            temperature_range = polynomial.find('prime:validRange', namespaces=ns)
            for bound in temperature_range.findall('prime:bound', namespaces=ns):
                if bound.attrib['kind'] == 'lower':
                    setattr(dj_thermo,
                            'lower_temp_bound_{0}'.format(polynomial_number),
                            float(bound.text))
                if bound.attrib['kind'] == 'upper':
                    setattr(dj_thermo,
                            'upper_temp_bound_{0}'.format(polynomial_number),
                            float(bound.text))
        if i == 0:
            logger.info("There was only one polynomial in {}/{}.xml!".format(sPrimeID, thpPrimeID))
            logger.info("Probably the temperature range was too small."
                  "We will make up a second one with no T range.")
            dj_thermo.lower_temp_bound_2 = dj_thermo.upper_temp_bound_1
            dj_thermo.upper_temp_bound_2 = dj_thermo.upper_temp_bound_1
            for j in range(1, 8):
                setattr(dj_thermo, 'coefficient_{0}_2'.format(j), 0.0)

        assert dj_thermo.upper_temp_bound_1 == dj_thermo.lower_temp_bound_2, "Temperatures don't match in the middle!"
        dj_thermo.save()


class PrimeTransportImporter(Importer):

    To import the transport data of a species. Left over from PrIMe importer

    prime_ID_prefix = 'tr'

    def import_elementtree_root(self, trans):
        ns = self.ns
        # Get the Prime ID for the transport data
        if trans.attrib.get("primeID") != 'tr00000000':
            trPrimeID = trans.attrib.get("primeID")
        else:
            return
        # Get the Prime ID for the species to which it belongs, and get (or create) the species
        specieslink = trans.find('prime:speciesLink', namespaces=ns)
        sPrimeID = specieslink.attrib['primeID']
        species, created = Species.objects.get_or_create(sPrimeID=sPrimeID)
        # Now get (or create) the django Transport object for that species
        dj_trans, created = Transport.objects.get_or_create(
            trPrimeID=trPrimeID,
            species=species)

        # Start by finding the source link, and looking it up in the bibliography
        bibliography_link = trans.find('prime:bibliographyLink',
                                       namespaces=ns)
        bPrimeID = bibliography_link.attrib['primeID']
        source, created = Source.objects.get_or_create(bPrimeID=bPrimeID)
        dj_trans.source = source
        # Now give the Transport object its other properties
        expression = trans.find('prime:expression', namespace=ns)
        for parameter in expression.findall('prime:parameter', namespaces=ns):
            if parameter.attrib['name'] == 'geometry':
                value = parameter.find('prime:value', namespaces=ns)
                dj_trans.geometry = float(value.text)
            elif parameter.attrib['name'] == 'potentialWellDepth':
                value = parameter.find('prime:value', namespaces=ns)
                dj_trans.potential_well_depth = float(value.text)
            elif parameter.attrib['name'] == 'collisionDiameter':
                value = parameter.find('prime:value', namespaces=ns)
                dj_trans.collision_diameter = float(value.text)
            elif parameter.attrib['name'] == 'dipoleMoment':
                value = parameter.find('prime:value', namespaces=ns)
                dj_trans.dipole_moment = float(value.text)
            elif parameter.attrib['name'] == 'polarizability':
                value = parameter.find('prime:value', namespaces=ns)
                dj_trans.polarizability = float(value.text)
            elif parameter.attrib['name'] == 'rotationalRelaxation':
                value = parameter.find('prime:value', namespaces=ns)
                dj_trans.rotational_relaxation = float(value.text)
        dj_trans.save


class PrimeReactionImporter(Importer):

    To import chemical reactions. Left over from PrIMe importer


    def import_elementtree_root(self, reaction):
        ns = self.ns
        primeID = reaction.attrib.get("primeID")
        dj_reaction, created = Reaction.objects.get_or_create(rPrimeID=primeID)
        reactants = reaction.find('prime:reactants',
                                  namespaces=ns).findall('prime:speciesLink',
                                                         namespaces=ns)
        stoichiometry_already_in_database = Stoichiometry.objects.all().filter(
            reaction=dj_reaction).exists()

        for reactant in reactants:
            species_primeID = reactant.attrib['primeID']
            dj_species, created = Species.objects.get_or_create(
                sPrimeID=species_primeID)
            stoichiometry = float(reactant.text)
            logger.debug("Stoichiometry of {} is {}".format(species_primeID,
                                                     stoichiometry))
            dj_stoich, created = Stoichiometry.objects.get_or_create(
                species=dj_species,
                reaction=dj_reaction,
                stoichiometry=stoichiometry)
            # This test currently broken or finds false failures:
            # if stoichiometry_already_in_database:
            #    assert not created, "Stoichiometry change detected! probably a mistake?"
            # import ipdb; ipdb.set_trace()


class PrimeKineticsImporter(Importer):

    To import the kinetics data of a reaction (can be multiple for each species). Left over from PrIMe importer

    prime_ID_prefix = 'rk'

    def import_elementtree_root(self, kin):
        ns = self.ns
        # Get the Prime ID for the kinetics
        if kin.attrib.get("primeID") != 'rk00000000':
            rkPrimeID = kin.attrib.get("primeID")
        else:
            return
        # Get the Prime ID for the reaction to which it belongs, and get (or create) the reaction
        reactionlink = kin.find('prime:reactionLink', namespaces=ns)
        rPrimeID = reactionlink.attrib['primeID']
        reaction, created = Reaction.objects.get_or_create(rPrimeID=rPrimeID)
        # Now get (or create) the django Kinetics object for that reaction
        kinetics, created = Kinetics.objects.get_or_create(
                                rkPrimeID=rkPrimeID,
                                reaction=reaction)

        # Start by finding the source link, and looking it up in the bibliography
        bibliography_link = kin.find('prime:bibliographyLink',
                                     namespaces=ns)
        bPrimeID = bibliography_link.attrib['primeID']
        source, created = Source.objects.get_or_create(bPrimeID=bPrimeID)
        kinetics.source = source

        # Now identify the type and try to make that objecttoo
        coefficient = kin.find('prime:rateCoefficient', namespaces=ns)

        # Now give the Kinetics object its other properties
        if coefficient is None:
            raise ImportError("Couldn't find coefficient (and we can't yet interpret linked rates)")
        if coefficient.attrib['direction'] == 'reverse':
            kinetics.is_reverse = True
        relunc = coefficient.find('prime:uncertainty', namespaces=ns)
        if relunc is not None:
            kinetics.relative_uncertainty = float(relunc.text)

        kinetics.save()

        # now find the expression(s) and create those
        expressions = coefficient.findall('prime:expression', namespaces=ns)
        if len(expressions) != 1:
            raise NotImplementedError("Can only do single expression (for now)")
        for expression in expressions:
            if expression.attrib['form'].lower() == 'arrhenius':
                ### ARRHENIUS
                arrhenius, created = ArrheniusKinetics.objects.get_or_create(
                    kinetics=kinetics)

                for parameter in expression.findall('prime:parameter', namespaces=ns):
                    if parameter.attrib['name'] == 'a' or parameter.attrib['name'] == 'A':
                        value = parameter.find('prime:value', namespaces=ns)
                        arrhenius.A_value = float(value.text)
                        try:
                            uncertainty = parameter.find('prime:uncertainty', namespaces=ns)
                            arrhenius.A_value_uncertainty = float(uncertainty.text)
                        except:
                            pass
                    elif parameter.attrib['name'] == 'n':
                        value = parameter.find('prime:value', namespaces=ns)
                        arrhenius.n_value = float(value.text)
                    elif parameter.attrib['name'] == 'e' or parameter.attrib['name'] == 'E':
                        value = parameter.find('prime:value', namespaces=ns)
                        arrhenius.E_value = float(value.text)
                        try:
                            uncertainty = parameter.find('prime:uncertainty', namespaces=ns)
                            arrhenius.E_value_uncertainty = float(uncertainty.text)
                        except:
                            pass
                temperature_range = kin.find('prime:validRange', namespaces=ns)
                if temperature_range is not None:
                    for bound in temperature_range.findall('prime:bound', namespaces=ns):
                        if bound.attrib['kind'] == 'lower':
                            arrhenius.lower_temp_bound = float(bound.text)
                        if bound.attrib['kind'] == 'upper':
                            arrhenius.upper_temp_bound = float(bound.text)
                arrhenius.save()

            #### HERE IS WHERE WE EXTEND FOR OTHER TYPES with elif statements
            else:
                raise NotImplementedError("Can't import kinetics type {}".format(expression.attrib['form']))


class PrimeModelImporter(Importer):

    To import kinetic models. Left over from PrIMe importer


    def import_elementtree_root(self, mod):
        ns = self.ns
        primeID = mod.attrib.get("primeID")
        dj_mod, created = KineticModel.objects.get_or_create(mPrimeID=primeID)
        # Start by finding the source link, and looking it up in the bibliography
        bibliography_link = mod.find('prime:bibliographyLink',
                                     namespaces=ns)
        bPrimeID = bibliography_link.attrib['primeID']
        source, created = Source.objects.get_or_create(bPrimeID=bPrimeID)
        dj_mod.source = source
        dj_mod.model_name = mod.findtext('prime:preferredKey',
                                         namespaces=ns,
                                         default='')
        # parse additional info
        additionalinfo = mod.find('prime:additionalDataItem', namespaces=ns)
        info = additionalinfo.text
        description = additionalinfo.attrib.get('description')
        if description != 'Model description':
            if info is not None:
                dj_mod.additional_info = description + " = " + info
            else:
                dj_mod.additional_info = description
        # parse species links
        species_set = mod.find('prime:speciesSet', namespaces=ns)
        specieslink = species_set.findall('prime:speciesLink', namespaces=ns)
        for species in specieslink:
            sPrimeID = species.attrib.get("primeID")
            thermolink = species.find('prime:thermodynamicDataLink', namespaces=ns)
            thpPrimeID = thermolink.attrib.get("primeID")
            transportlink = species.find('prime:transportDataLink', namespaces=ns)
            if transportlink is not None:
                trPrimeID = transportlink.attrib.get("primeID")

        # parse reaction links
        reaction_set = mod.find('prime:reactionSet', namespaces=ns)
        reactionlink = reaction_set.findall('prime:reactionLink', namespaces=ns)
        for reaction in reactionlink:
            rPrimeID = reaction.attrib.get("primeID")
            reversible = reaction.attrib.get("reversible")
            kineticslink = reaction.find('prime:reactionRateLink', namespaces=ns)
            rkPrimeID = kineticslink.attrib.get("primeID")
"""


def findLibraryFiles(path):

    thermoLibs = []
    kineticsLibs = []
    for root, dirs, files in os.walk(path):
        for name in files:
            path = os.path.join(root, name)
            if root.endswith('RMG-Py-thermo-library') and name == 'ThermoLibrary.py':
                logger.info("Found thermo library {0}".format(path))
                thermoLibs.append(path)
            elif root.endswith('RMG-Py-kinetics-library') and name == 'reactions.py':
                logger.info("Found kinetics file {0}".format(path))
                kineticsLibs.append(path)
            else:
                logger.debug('{0} unread because it is not named like a kinetics or thermo '
                              'library generated by the chemkin importer'.format(path))
    return thermoLibs, kineticsLibs


def main(args):
    """
    The main function. Give it the path to the top of the database mirror
    """

    logger.debug("Entering the \"main\" function...")

    with open('errors.txt', "w") as errors:
        errors.write("Restarting import at " + time.strftime("%x"))
    logger.debug("Importing models from", str(args.paths))

    thermo_libraries = []
    kinetics_libraries = []
    for path in args.paths:
        t, k = findLibraryFiles(path)
        thermo_libraries.extend(t)
        kinetics_libraries.extend(k)

    logger.debug("Found {} thermo libraries: \n - {}".format(len(thermo_libraries), '\n - '.join(thermo_libraries)))
        
    for filepath in thermo_libraries:
        logger.info("Importing thermo library from {}".format(filepath))
        importer = ThermoLibraryImporter(filepath)
        importer.load_library()
        importer.import_species()
        importer.import_data()

    logger.info('Exited thermo imports!')

    logger.debug("Found {} kinetics libraries: \n - {}".format(len(kinetics_libraries),
                                                                '\n - '.join(kinetics_libraries)))

    for filepath in kinetics_libraries:
        logger.info("Importing kinetics library from {}".format(filepath))
        importer = KineticsLibraryImporter(filepath)
        importer.load_library()
        importer.import_data()  # TODO -- Actually write

    logger.info('Exited kinetics imports!')


"""
MAIN FUNCTION CALL
"""

if __name__ == "__main__":
    # Configure Logging for the Import
    logger = logging.getLogger('THE_LOG')
    logger.setLevel(logging.DEBUG)

    file_printer = logging.FileHandler('rmg_models_importer_log.txt')
    file_printer.setLevel(logging.INFO)
    console_printer = logging.StreamHandler()
    console_printer.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    file_printer.setFormatter(formatter)
    console_printer.setFormatter(formatter)

    logger.addHandler(file_printer)
    logger.addHandler(console_printer)

    logger.info("STARTING LOGGING FOR RMG IMPORTER RUN ON {}".format(datetime.datetime.now()))
    logger.debug("Parsing the Command Line Arguments...")
    parser = argparse.ArgumentParser(
        description='Import RMG models into Django.')
    parser.add_argument('paths',
                        metavar='path',
                        type=str,
                        nargs='+',
                        help='the path(s) to search for kinetic models')
    args = parser.parse_args()
    args.paths = [os.path.expandvars(path) for path in args.paths]

    logger.debug("Beginning the import...")
    main(args)
    logger.info("Exited main function successfully!")

    # Close the log handlers
    file_printer.close()
    console_printer.close()





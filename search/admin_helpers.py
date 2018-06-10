from django.db import connections, IntegrityError, DatabaseError
from django.utils import timezone
from .models import *
import datetime
import csv
from decimal import *
from io import TextIOWrapper
from . import phenotype_encoding as pe


def add_individual(centre, centre_id, collection=None, phenotypes=None):
    try:
        source = Source.objects.get(source_name=centre)
    except Source.DoesNotExist:
        raise Exception(f'Can\'t find source in database {centre}')

    ## check if the id has already been entered for the given source
    if IndividualIdentifier.objects.filter(individual_string=centre_id,source_id=source.id).count() > 0:
        raise Exception(f"Individual '{centre_id}' already added for this source")
    
    ## an empty active_id field means that the object refers to itself!
    ## if the active_id field is not empty, that means it refers to another individual object
    ind = Individual()                
    ind.date_created = timezone.now()
    ind.last_updated = timezone.now()
    ind.save()                    
    
    ## create the phenodb_id
    pdbId = PhenodbIdentifier()
    pdbId.individual = ind
    pdbId.phenodb_id = u"pdb" + str(ind.pk)
    pdbId.date_created = timezone.now()
    pdbId.last_updated = timezone.now()
    pdbId.save()
    
    if collection:
        try:
            coll = Collection.objects.get(collection_name=collection)
        except Collection.DoesNotExist:
            raise Exception(f"Can't find collection in database '{collection}'")
            collection = None
        except KeyError:
            collection = None
    
    if collection:
        indColl = IndividualCollection()
        indColl.individual = ind
        indColl.collection = coll
        indColl.date_created = timezone.now()
        indColl.last_updated = timezone.now()
        indColl.save()
          
    # insert the individual identifier
    indId = IndividualIdentifier()
    indId.individual = ind
    indId.individual_string = centre_id
    indId.source = source
    indId.date_created = timezone.now()
    indId.last_updated = timezone.now()
    try:
        indId.save()
    except IntegrityError:
        raise Exception(f"centre_id {centre_id} is already in the database")

    # insert phenotype values
    if phenotypes:
        for phenotype_name, phenotype_value in phenotypes.items():
            saveUpdatePhenotype(
                phenotype_value=phenotype_value,
                phenotype_name=phenotype_name,
                individual=ind,
                individual_identifier=indId
            )

def add_sample(centre, centre_id, sample_id):
    try:
        source = Source.objects.get(source_name=centre)
    except Source.DoesNotExist:
        raise Exception(u"Can't find source in database '" + centre + u"'")
    
    # check if the id has already been entered for the given source
    try:
        sampleIndId = IndividualIdentifier.objects.get(individual_string=centre_id,source_id=source.id)
    except IndividualIdentifier.DoesNotExist:
        raise Exception(u"Individual " + centre_id + u" NOT found in phenodb")
    
    ## check that a sample has not already been entered for the ind with the same name
    if Sample.objects.filter(individual=sampleIndId.individual,sample_id=sample_id).count() > 0:
        raise Exception(u"Sample ID '" + sample_id + u"' already added for this individual")

    sample = Sample()
    sample.individual = sampleIndId.individual
    sample.sample_id = sample_id
    sample.date_created = timezone.now()
    sample.last_updated = timezone.now()
    
    warehouseCursor = connections['warehouse'].cursor()
    
    ## if the sanger warehouse is not available then skip this step and warn the user
    try: 
        q = f"SELECT DISTINCT sanger_sample_id, supplier_name, gender FROM current_samples WHERE name = '{sample.sample_id}' ORDER BY checked_at desc;"
        warehouseCursor.execute(q)
        row = warehouseCursor.fetchone()
        if not row or not row[0]:
            raise Exception(u"Sample " + sample.sample_id + u" NOT found in warehouse")  
        if row[1] != sampleIndId.individual_string:
            raise Exception(u"supplier name " + str(sampleIndId.individual_string) + u" does not match warehouse "  + row[1])
    except DatabaseError as e:
        raise Exception(e)
    try:
        sample.save()
    except IntegrityError:
        pass
    
    ## now the sample is inserted check if it was a missing sample
    if MissingSampleID.objects.filter(sample_id=sample_id).count() > 0:
        missingSamples = MissingSampleID.objects.filter(sample_id=sample_id)
        
        for missingSample in missingSamples:
            
            studySample = StudySample()
            studySample.sample = sample
            studySample.study = missingSample.study
            studySample.date_created = timezone.now()
            studySample.last_updated = timezone.now()

            try:
                studySample.save()
            except IntegrityError:
                continue
                
            missingSample.delete()

def add_phenotype_values(centre, centre_id, phenotypes):
    try:
        source = Source.objects.get(source_name=centre)
    except Source.DoesNotExist:
        raise Exception(u"Can't find source in database '" + centre + u"'")

    # get the individual
    try:
        sampleIndId = IndividualIdentifier.objects.get(individual_string=centre_id,source_id=source.id)
    except IndividualIdentifier.DoesNotExist:
        raise Exception(u"Individual " + centre_id + u" NOT found in phenodb")

    ind = sampleIndId.individual

    for phenotype_name, phenotype_value in phenotypes.items():
        saveUpdatePhenotype(
            phenotype_value=phenotype_value,
            phenotype_name=phenotype_name,
            individual=ind,
            individual_identifier=sampleIndId
        )
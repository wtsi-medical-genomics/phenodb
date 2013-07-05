from django import forms
from search.models import *
from django.contrib import admin
import datetime
from django.utils.timezone import utc
import csv
from django.db import connections
from decimal import *
from django.db import IntegrityError, DatabaseError
from django.contrib import messages
from django.db import transaction


class BulkUploadForm(forms.ModelForm):
    
    import_options = (
        ('phenotypes','Phenotypes'),
        ('sources','Sources'),
        ('individuals','Individuals'),        
        ('samples','Samples'),                
        ('study_samples', 'Study Samples'),
        ('sample_qc', 'Sample QC'),
        ('add_sample_on_sample', 'Add New SampleID to existing Sample on SampleID'),
        ('add_phenotype_values', 'Add phenotype values to existing individuals')
        #('check_samples_in_warehouse', 'Check Samples in Sanger Warehouse'),
    )
    import_data_type = forms.ChoiceField(import_options, help_text = "Select the type of data you wish to import")
    
    file_format_description = """
    <b>File Formats:</b><br>
    Column Headings:&ltrequired_column&gt [optional_column] - The columns may be in any order however the column headings must match the required values <br>

    <b>Phenotypes</b><br>
    &nbsp&nbsp&ltname&gt &lttype&gt &ltdescription&gt <br>
    
    <b>Sources</b><br>
    &nbsp&nbsp&ltcentre&gt &ltcontact&gt &ltdescription&gt <br>
    
    <b>Individuals</b><br>
    &nbsp&nbsp&ltcentre&gt &ltcentre_id&gt [collection] [any Phenotype name already entered in the Phenotype table]...<br>
    
    <b>Samples</b><br>
    &nbsp&nbsp&ltsample_id&gt &ltcentre&gt &ltcentre_id&gt <br>
    
    <b>Study Samples</b><br>    
    &nbsp&nbspOne sample_id per line, select the study from the dropdown menu <br>
    
    <b>Sample QC</b><br>
    &nbsp&nbsp&ltsample_id&gt &ltqc_value&gt<br>
    &nbsp&nbspQC_values should be 0 (Fail) or 1 (Pass), select the QC and Study from the dropdown menus <br>
    
    <b>New Sample ID on existing Sample</b><br>
    &nbsp&nbsp&ltsample_id&gt &ltnew_sample_id&gt <br>
    
    <b>Add Phenotype to existing Individual</b><br>
    &nbsp&nbsp&ltcentre&gt &ltcentre_id&gt [any Phenotype name already entered in the Phenotype table]... <br>
    
    """
    file_to_import = forms.FileField(help_text = file_format_description)
    
    delimiter_options = (
        ('comma', 'Comma'),
        ('tab','Tab')
        
    )    
    file_delimiter = forms.ChoiceField(delimiter_options, help_text = "Select the delimeter used in the file")
    
    study_id = forms.ModelChoiceField(Study.objects.all(), required=False, help_text = "Only required when adding Study Samples")
    qc_id = forms.ModelChoiceField(QC.objects.all(), required=False, help_text = "Only required when adding Samples QC values")

    class Meta:
        model = BulkUpload

class BulkUploadAdmin(admin.ModelAdmin):
    
    form = BulkUploadForm
    true_list = ["Yes", "yes", "true", "True", "1", "Affected", "affected"]
    false_list = ["No", "no", "false", "False", "0", "Unaffected", "unaffected"]
    
    #Overrides model object saving.
    def save_model(self, request, obj, form, change):
        
        import_data_type = request.POST["import_data_type"]
        file_delimiter = request.POST["file_delimiter"]
        
        if import_data_type == "study_samples":                
            
            study = Study.objects.get(id=request.POST["study_id"])
            
            sample_total = 0;
            insert_total = 0;
            
            for line in request.FILES["file_to_import"]:
                
                sample_total += 1                
                sample_id = line.strip()
                
                if Sample.objects.filter(sample_id=sample_id).count() > 0:
                    sample = Sample.objects.filter(sample_id=sample_id)[0]
                else:
                    ## make sure the string in not empty
                    if sample_id:
                        missingSampleID = MissingSampleID();
                        missingSampleID.sample_id = sample_id
                        missingSampleID.study = study
                        try:
                            missingSampleID.save()
                        except IntegrityError:
                            ## already entered in the database so just pass
                            pass
                    
                    continue
                
                studySample = StudySample()
                studySample.sample = sample
                studySample.study = study
                studySample.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                studySample.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)     
                
                try:
                    studySample.save()
                except IntegrityError:
                    continue
                
                insert_total += 1
            
            messages.error(request, str(insert_total) + " of " + str(sample_total) + u" samples successfully inserted into the database")
            return
        
        elif import_data_type == "sample_qc":
            
            study_id = request.POST["study_id"]
            qc_id    = request.POST["qc_id"]
            
            study = Study.objects.get(id=study_id)
            qc    = QC.objects.get(id=qc_id)
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
            
            for line in records:
                
                ## required columns: Centre,Centre ID                
                try:
                    sample_id = line['sample_id']
                    qc_value = line['qc_value']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'sample_id qc_value'")
                    return     
                
                try:
                    sample = Sample.objects.get(sample_id=sample_id)
                except Sample.DoesNotExist:
                    messages.error(request, u"Can't find sample in database '" + sample_id + u"'")
                    continue                                
                
                try:
                    study_sample = StudySample.objects.get(sample=sample,study=study)
                except Sample.DoesNotExist:
                    messages.error(request, u"Can't find study sample in database '" + sample_id + u"' '" + study.study_name + u"'")
                    continue
                
                
                sampleQC = SampleQC()
                sampleQC.qc = qc
                sampleQC.study_sample = study_sample
                if qc_value == '1':
                    sampleQC.qc_pass = True
                else:
                    sampleQC.qc_pass = False                    
                sampleQC.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                sampleQC.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)                
                
                try:
                    sampleQC.save()
                except IntegrityError, err:
                    messages.error(request, u"Sample " + sample_id + " and study " + study_id + " is already in the database " + str(err))
                    continue        
            return
            
        elif import_data_type == "individuals":
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
            
            for line in records:
                try:
                    centre = line['centre']
                    centre_id = line['centre_id']
                    sample_id = line['sample_id']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre centre_id'")
                    return     
                
                try:
                    source = Source.objects.get(source_name=centre)
                except Source.DoesNotExist:
                    messages.error(request, u"Can't find source in database '" + centre + u"'")
                    continue
                               
                ## check if the id has already been entered for the given source
                if IndividualIdentifier.objects.filter(individual_string=centre_id,source_id=source.id).count() > 0:
                    messages.error(request, u"Individual '" + centre_id + u"' already added for this source")
                    continue
                
                ## the individual id from another file might be similar but not exactly the same
                ## check if the sample id and source are the same, if they are then add an individual identifier
                
                try:
                    if Sample.objects.get(sample_id=sample_id):
                
                        sample = Sample.objects.get(sample_id=sample_id)
                        if IndividualIdentifier.objects.get(individual=sample.individual, source__source_name=centre):
                        
                            ## add a individual identifier
                            indId = IndividualIdentifier()
                            indId.individual = sample.individual
                            indId.individual_string = centre_id                
                            indId.source = source
                            indId.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                            indId.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)                
                            try:
                                indId.save()
                            except IntegrityError:
                                messages.error(request, u"centre_id " + centre_id + " is already in the database")
                            continue
                except Sample.DoesNotExist:
                    pass
                
                ## an empty active_id field means that the object refers to itself!
                ## if the active_id field is not empty, that means it refers to another individual object
                ind = Individual()                
                ind.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                ind.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                ind.save()                    
                
                ## create the phenodb_id
                pdbId = PhenodbIdentifier()
                pdbId.individual = ind
                pdbId.phenodb_id = u"pdb" + str(ind.pk)
                pdbId.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                pdbId.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                pdbId.save()
                
                try:
                    collection = line['collection']
                    coll = Collection.objects.get(collection_name=collection)
                except Collection.DoesNotExist:
                    messages.error(request, u"Can't find collection in database '" + collection + u"'")
                    collection = None
                except KeyError:
                    collection = None
                    
                if collection is not None:
                    indColl = IndividualCollection()
                    indColl.individual = ind
                    indColl.collection = coll
                    indColl.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                    indColl.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                    indColl.save()
                      
                ## insert the individual identifier
                indId = IndividualIdentifier()
                indId.individual = ind
                indId.individual_string = centre_id                
                indId.source = source
                indId.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                indId.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)                
                try:
                    indId.save()
                except IntegrityError:
                    messages.error(request, u"centre_id " + centre_id + " is already in the database")
                    continue
                                        
                ## insert phenotype values
                for col in line:                      
                    try:   
                        if len(line[col]) == 0:
                            continue
                    except TypeError:
                        ## vale is None
                        continue
                                   
                    try:
                        pheno = Phenotype.objects.get(phenotype_name=col)
                    except Phenotype.DoesNotExist:
#                        messages.error(request, u"Warning Can't find phenotype '" + col + "' in database")
                        continue
                    
                    if pheno.phenotype_type.phenotype_type == u"Affection Status":
                        affectVal = AffectionStatusPhenotypeValue()
                        affectVal.phenotype = pheno
                        affectVal.individual = ind
                        ## if the value is empty or no set as false
                        if line[col] in BulkUploadAdmin.false_list:
                            affectVal.phenotype_value = False
                        elif line[col] in BulkUploadAdmin.true_list:
                            affectVal.phenotype_value = True
                        else:
                            continue
                        affectVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        affectVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            affectVal.save()
                        except:
                            messages.error(request, u"failed to save " + pheno.phenotype_name)           
                    elif pheno.phenotype_type.phenotype_type == u"Qualitative":
                        qualVal = QualitativePhenotypeValue()
                        qualVal.phenotype = pheno
                        qualVal.individual = ind
                        qualVal.phenotype_value = line[col].strip()
                        qualVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        qualVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            qualVal.save()
                        except:
                            messages.error(request, u"failed to save " + pheno.phenotype_name)
                    elif pheno.phenotype_type.phenotype_type == u"Quantitative":
                        quantVal = QuantitiatvePhenotypeValue()
                        quantVal.phenotype = pheno
                        quantVal.individual = ind
                        ## special case for sex as this often needs to be parsed
                        if pheno.phenotype_name == "Sex":
                            if not str.isdigit(line[col]):
                                if str.lower(line[col]) == "female" or str.lower(line[col]) == "f":
                                    sex = 2
                                elif str.lower(line[col]) == "male" or str.lower(line[col]) == "m":
                                    sex = 1
                                else:
                                    sex = 0
                            else:
                                sex = line[col]
                            quantVal.phenotype_value = Decimal(sex)
                        else:
                            if str.isdigit(line[col]) == False:
                                continue
                            quantVal.phenotype_value = Decimal(line[col])                            
                        quantVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        quantVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            quantVal.save()
                        except:
                            messages.error(request, u"failed to save " + pheno.phenotype_name)
                    else:
                        messages.error(request, u"unrecognised phenotype type " + pheno.phenotype_type.phenotype_type)
                        
                    transaction.commit()
            return
            
        elif import_data_type == "phenotypes":
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
            
            for line in records:
                try:
                    name = line['name']
                    type = line['type']
                    description = line['description']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'name type description'")
                    return    
                
                try:
                    phenoType = PhenotypeType.objects.get(phenotype_type=type)
                except PhenotypeType.DoesNotExist:
                    messages.error(request, u"Phenotype Type " + type + u" was NOT found in phenodb for " + name)
                    continue
                         
                pheno = Phenotype()
                pheno.phenotype_name = name
                pheno.phenotype_type = phenoType
                pheno.phenotype_description = description
                
                try:
                    pheno.save()
                except IntegrityError:
                    messages.error(request, u"Phenotype " + line['name'] + " is already in the database")
                    continue
                messages.success(request, u"Phenotype " + line['name'] + u" was added to PhenoDB")
            return
        
        elif import_data_type == "sources":
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
            
            for line in records:
                try:
                    name = line['centre']
                    contact = line['contact']
                    description = line['description']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre contact description'")
                    return 
                
                source = Source()
                source.source_name = name
                source.contact_name = contact
                source.source_description = description
                try:
                    source.save()
                except IntegrityError:
                    messages.error(request, u"Source " + line['centre'] + " is already in the database")
                    continue
                messages.success(request, u"Source " + line['centre'] + u" was added to PhenoDB")                
            return
        
        elif import_data_type == "samples":
            
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
            
            for line in records:
                
                try:
                    centre = line['centre']
                    centre_id = line['centre_id']
                    sample_id = line['sample_id']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre centre_id sample_id'")
                    return     
                
                try:
                    source = Source.objects.get(source_name=centre)
                except Source.DoesNotExist:
                    messages.error(request, u"Can't find source in database '" + centre + u"'")
                    continue                
                
                ## check if the id has already been entered for the given source
                try:
                    sampleIndId = IndividualIdentifier.objects.get(individual_string=centre_id,source_id=source.id)
                except IndividualIdentifier.DoesNotExist:
                    messages.error(request, u"Individual " + centre_id + u" NOT found in phenodb")
                    continue
                
                ## check that a sample has not already been entered for the ind with the same name
                if Sample.objects.filter(individual=sampleIndId.individual,sample_id=sample_id).count() > 0:
                    messages.error(request, u"Sample ID '" + sample_id + u"' already added for this individual")                
                    continue
                          
                sample = Sample()
                sample.individual = sampleIndId.individual
                sample.sample_id = sample_id
                sample.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                sample.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                
                warehouseCursor = connections['warehouse'].cursor()
                
                ## if the sanger warehouse is not available then skip this step and warn the user
                try: 
                    warehouseCursor.execute("SELECT DISTINCT sanger_sample_id, supplier_name, gender FROM samples WHERE name = %s ORDER BY checked_at desc", sample.sample_id)
                    row = warehouseCursor.fetchone()
                    if row is None:
                        messages.error(request, u"Sample " + sample.sample_id + u" NOT found in warehouse")  
                        continue
                    if row[0] is None:
                        messages.error(request, u"Sample " + sample.sample_id + u" NOT found in warehouse")
                        continue  
                    if row[1] != sampleIndId.individual_string:
                        messages.error(request, u"supplier name " + str(sampleIndId.individual_string) + u" does not match warehouse "  + row[1])                        
                        
                        ## insert the new individual identifier
                        indId = IndividualIdentifier()
                        indId.individual = sampleIndId.individual
                        indId.individual_string = row[1]
                        indId.source = source
                        indId.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        indId.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            indId.save()
                        except IntegrityError:
                            pass
                except DatabaseError:
                    messages.error(request, u"Can't connect to warehouse database")                    
                                                                                                           
                try:
                    sample.save()
                except IntegrityError:
#                   messages.error(request, u"Sample " + sample_id + " is already in the database")
                    continue
                transaction.commit()
                
                ## now the sample is inserted check if it was a missing sample
                if MissingSampleID.objects.filter(sample_id=sample_id).count() > 0:
                    missingSamples = MissingSampleID.objects.filter(sample_id=sample_id)
                    
                    for missingSample in missingSamples:
                        
                        studySample = StudySample()
                        studySample.sample = sample
                        studySample.study = missingSample.study
                        studySample.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        studySample.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)     
                
                        try:
                            studySample.save()
                        except IntegrityError:
                            continue
                        
                        missingSample.delete()
                
            return
        
        elif import_data_type == "add_sample_on_sample":
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
                
            for line in records:  
  
                try:
                    sample_id = line['sample_id']     
                    new_sample_id = line['new_sample_id']                                                       
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'sample_id','new_sample_id'")
                    return
                
                if Sample.objects.filter(sample_id=sample_id).count() > 0:                    
                    sample = Sample.objects.filter(sample_id=sample_id)[0]                
                else:
                    continue
                
                try:
                    individual = Individual.objects.get(id=sample.individual.id)
                except Individual.DoesNotExist:
#                       messages.error(request, u"Can't find sample in database '" + sample_id + u"'")
                    continue 
                
                    ## check if this sample has already been added for this individual
                if Sample.objects.filter(sample_id=new_sample_id, individual=individual.id).count() > 0:
                    messages.error(request, u"sample_id '" + new_sample_id + u"' already added for this individual")
                    continue
                
                newSample = Sample()
                newSample.individual = individual
                newSample.sample_id = new_sample_id
                newSample.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                newSample.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                newSample.save()
                transaction.commit()
            return
            
        elif import_data_type == "add_phenotype_values":
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
            
            for line in records:   
                
                try:
                    centre = line['centre']
                    centre_id = line['centre_id']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre centre_id'")
                    return
                
                try:
                    source = Source.objects.get(source_name=centre)
                except Source.DoesNotExist:
                    messages.error(request, u"Can't find source in database '" + centre + u"'")
                    continue 
                
                ## get the individual
                try:
                    sampleIndId = IndividualIdentifier.objects.get(individual_string=centre_id,source_id=source.id)
                except IndividualIdentifier.DoesNotExist:
                    messages.error(request, u"Individual " + centre_id + u" NOT found in phenodb")
                    continue
                
                ind = sampleIndId.individual                
                
                for col in line:                      
                    try:   
                        if len(line[col]) == 0:
                            continue
                    except TypeError:
                        ## vale is None
                        continue
                                   
                    try:
                        pheno = Phenotype.objects.get(phenotype_name=col)
                    except Phenotype.DoesNotExist:
#                        messages.error(request, u"Warning Can't find phenotype '" + col + "' in database")
                        continue
                    
                    if pheno.phenotype_type.phenotype_type == u"Affection Status":
                        
                        if line[col] in BulkUploadAdmin.false_list:
                            phenotype_value = False
                        elif line[col] in BulkUploadAdmin.true_list:
                            phenotype_value = True
                        else:
                            continue
                        
                        ## update or create
                        if AffectionStatusPhenotypeValue.objects.filter(phenotype=pheno, individual=ind).exists():
                            affectVal = AffectionStatusPhenotypeValue.objects.get(phenotype=pheno, individual=ind)
                            affectVal.phenotype_value = phenotype_value
                        else:
                            affectVal = AffectionStatusPhenotypeValue()
                            affectVal.phenotype = pheno
                            affectVal.individual = ind
                            affectVal.phenotype_value = phenotype_value
                            affectVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                            affectVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            affectVal.save()
                        except:
                            messages.error(request, u"failed to update " + pheno.phenotype_name + " for " + sampleIndId.individual_string)
                        
                    elif pheno.phenotype_type.phenotype_type == u"Qualitative":
                        
                        phenotype_value = line[col].strip()
                        
                        if QualitativePhenotypeValue.objects.filter(phenotype=pheno, individual=ind).exists():
                            qualVal = QualitativePhenotypeValue.objects.get(phenotype=pheno, individual=ind)
                            qualVal.phenotype_value = phenotype_value
                        else:
                            qualVal = QualitativePhenotypeValue()
                            qualVal.phenotype = pheno
                            qualVal.individual = ind
                            qualVal.phenotype_value = phenotype_value
                            qualVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                            qualVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)                        
                        try:
                            qualVal.save()
                        except:
                            messages.error(request, u"failed to update " + pheno.phenotype_name + " for " + sampleIndId.individual_string)
                    elif pheno.phenotype_type.phenotype_type == u"Quantitative":
                        
                        ## special case for sex as this often needs to be parsed
                        if pheno.phenotype_name == "Sex":
                            if not str.isdigit(line[col]):
                                if str.lower(line[col]) == "female":
                                    sex = 2
                                elif str.lower(line[col]) == "male":
                                    sex = 1
                                else:
                                    sex = 0
                            else:
                                sex = line[col]
                            phenotype_value = Decimal(sex)
                        else:
                            if str.isdigit(line[col]) == False:
                                continue
                            phenotype_value = Decimal(line[col])
                            
                        if QuantitiatvePhenotypeValue.objects.filter(phenotype=pheno, individual=ind).exists():
                            quantVal = QuantitiatvePhenotypeValue.objects.get(phenotype=pheno, individual=ind)
                            quantVal.phenotype_value = phenotype_value
                        else:
                            quantVal = QuantitiatvePhenotypeValue()
                            quantVal.phenotype = pheno
                            quantVal.individual = ind
                            quantVal.phenotype_value = phenotype_value
                            quantVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                            quantVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            quantVal.save()
                        except:
                            messages.error(request, u"failed to update " + pheno.phenotype_name + " for " + sampleIndId.individual_string)
                    else:
                        messages.error(request, u"unrecognised phenotype type " + pheno.phenotype_type.phenotype_type)
            return
        
        elif import_data_type == "check_samples_in_warehouse":
            
            if file_delimiter == "tab":
                records = csv.DictReader(request.FILES["file_to_import"], delimiter='\t')
            else:
                records = csv.DictReader(request.FILES["file_to_import"])
        
            for line in records:
                           
                try:
                    sample_id = line['sample_id']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'sample_id'")
                    return     
    
                if Sample.objects.filter(sample_id=sample_id).exists(): 
                    continue
                else:
                    warehouseCursor.execute("SELECT DISTINCT sanger_sample_id, supplier_name, cohort, country_of_origin, geographical_region  FROM samples WHERE name = %s ORDER BY checked_at desc", sample_id)
                    row = warehouseCursor.fetchone()
                    if row is None or row[0] is None:
#                        out_file.write(sample_id + " NOT in warehouse\n")
                        continue
                    else:
#                        out_file.write(str(row) + "\n")
                        continue
                                                            
            return

class PlatformAdmin(admin.ModelAdmin):
    list_display = ('platform_name', 'platform_type', 'platform_description')

class PhenotypeAdmin(admin.ModelAdmin):
    list_display = ('phenotype_name', 'phenotype_type', 'phenotype_description')                     
                     
class StudyAdmin(admin.ModelAdmin):
    list_display = ('study_name', 'platform', 'study_description')
    
class SourceAdmin(admin.ModelAdmin):
    list_display = ('source_name', 'contact_name', 'source_description')
    
class QCAdmin(admin.ModelAdmin):
    list_display = ('qc_name', 'qc_description')
                          
admin.site.register(Platform, PlatformAdmin)
admin.site.register(PlatformType)
admin.site.register(PhenotypeType)
admin.site.register(Phenotype, PhenotypeAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(QC, QCAdmin)
admin.site.register(BulkUpload, BulkUploadAdmin)
admin.site.register(Collection)

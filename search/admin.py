from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib import admin, messages
from django.db import connections, IntegrityError, DatabaseError
from .models import *
import datetime
import csv
from decimal import *
from io import TextIOWrapper
from . import phenotype_encoding as pe
from . import admin_helpers as helpers


def read_csv(csvFile, delimiter):
    # pdb.set_trace()
    f = TextIOWrapper(csvFile.file, encoding='UTF-8')
    if delimiter in ['tab', '\t']:
        reader = csv.DictReader(f, delimiter='\t')
    else:
        reader = csv.DictReader(f)
    for row in reader:
        yield(row)

class BulkUploadForm(forms.ModelForm):
    
    # fields
    import_options = (
        ('phenotypes','Phenotypes'),
        ('sources','Sources'),
        ('individuals','Individuals'),        
        ('individual_ids', 'Add new Individual IDs to an Individual'),
        ('remove_ind_dups','Remove Duplicate Individuals'),
        ('samples','Samples'),                
        ('study_samples', 'Study Samples'),
        ('sample_qc', 'Sample QC'),
        ('add_sample_on_sample', 'Add New SampleID to existing Sample on SampleID'),
        ('add_phenotype_values', 'Add phenotype values to existing individuals'),
        
#         ('add_sample_feature_values', 'Add sample feature values')
#         ('check_samples_in_warehouse', 'Check Samples in Sanger Warehouse'),
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
    
    <b>Add new Individual ID to an Individual</b><br>
    &nbsp&nbsp&ltcentre&gt &ltcentre_id&gt &ltnew_centre_id&gt <br>
    
    <b>Remove Duplicate Individuals</b><br>
    &nbsp&nbsp&ltcentre&gt &ltworking_id&gt &ltremove_id&gt <br>
    Given a working ID, Remove ID and Centre name this function will:<br>
    1. Search that both IDs exist in the database<br>
    2. Find the database individual_id that corresponds to the working and remove IDs<br>
    3. Update all the the IndividualIdentifier and Sample entries that use the remove_id individual_id with the working_id individual_id<br>
    4. Finally delete the PhenodbIdentifier and Individual entries corresponding to the remove_id individual_id <br>
    
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

    # class Meta:
    #     model = BulkUpload

class BulkUploadAdmin(admin.ModelAdmin):
    
    form = BulkUploadForm
    
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
                studySample.date_created = timezone.now()
                studySample.last_updated = timezone.now()     
                
                try:
                    studySample.save()
                except IntegrityError:
                    continue
                
                insert_total += 1
            
            messages.error(request, str(insert_total) + " of " + str(sample_total) + u" samples successfully inserted into the database")
            return
        
        elif import_data_type == 'remove_ind_dups':
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            
            for line in records:
                try:
                    working_id = line['working_id']
                    remove_id = line['remove_id'] 
                    centre = line['centre']
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'working_id remove_id centre'")
                    return
                
                try:
                    source = Source.objects.get(source_name=centre)
                except Source.DoesNotExist:
                    messages.error(request, u"Can't find source in database '" + centre + u"'")
                    continue
                
                print(IndividualIdentifier.objects.filter(individual_string=working_id,source_id=source.id).count())
                
                ## check that the working ID exists
                if IndividualIdentifier.objects.filter(individual_string=working_id,source_id=source.id).count() < 1:
                    messages.error(request, u"Working ID '" + working_id + u"' does not exist in the database")
                    continue
                
                ## check that the remove ID exists
                if IndividualIdentifier.objects.filter(individual_string=remove_id,source_id=source.id).count() < 1:
                    messages.error(request, u"Remove ID '" + remove_id + u"' does not exist in the database")
                    continue
                
                ## get the indivdual indentifier object of the working ID
                workingIndividualIdentifier = IndividualIdentifier.objects.get(individual_string=working_id,source_id=source.id)
                
                ## get the indivdual indentifier object of the remove ID
                removeIndividualIdentifier = IndividualIdentifier.objects.get(individual_string=remove_id,source_id=source.id)
                
                ## update all the individual identifiers to point to the working_id individual_id
                for individualIdentifer in IndividualIdentifier.objects.filter(individual_id=removeIndividualIdentifier.individual_id):
                    
                    individualIdentifer.individual_id = workingIndividualIdentifier.individual_id
                
                ## update all the samples to point to the working_id individual_id
                for sample in Sample.objects.filter(individual_id=removeIndividualIdentifier.individual_id):
                    
                    sample.individual_id = workingIndividualIdentifier.individual_id
                
                ## remove the phenodb_id
                PhenodbIdentifier.objects.get(individual_id=removeIndividualIdentifier.individual_id).delete()
                
                ## remove the individual
                Individual.objects.get(id=removeIndividualIdentifier.individual_id).delete()
             
            return
        
        elif import_data_type == "sample_qc":
            
            study_id = request.POST["study_id"]
            qc_id    = request.POST["qc_id"]
            
            study = Study.objects.get(id=study_id)
            qc    = QC.objects.get(id=qc_id)
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            
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
                sampleQC.date_created = timezone.now()
                sampleQC.last_updated = timezone.now()                
                
                try:
                    sampleQC.save()
                except IntegrityError as err:
                    messages.error(request, u"Sample " + sample_id + " and study " + study_id + " is already in the database " + str(err))
                    continue        
            return
            
        elif import_data_type == "individuals":
            # import pdb; pdb.set_trace()
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            
            for line in records:
                try:
                    centre = line['centre']
                    centre_id = line['centre_id']
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre centre_id'")
                    return
                try:
                    collection = line['collection']
                except KeyError:
                    collection = None

                phenotypes = {}
                for col in line:
                    if col not in ['centre', 'centre_id', 'collection']:
                        phenotypes[col] = line[col]

                try:
                    helpers.add_individual(
                        centre=centre,
                        centre_id=centre_id, 
                        collection=collection,
                        phenotypes=phenotypes
                    )
                except Exception as e:
                    messages.error(request, e)
            return
            
        elif import_data_type == "phenotypes":
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            
            for line in records:
                try:
                    name = line['name']
                    ptype = line['type']
                    description = line['description']
                except KeyError:
                    messages.error(request, "Input file is missing required column(s) 'name type description'")
                    return
                try:
                    phenoType = PhenotypeType.objects.get(phenotype_type=ptype)
                except PhenotypeType.DoesNotExist:
                    messages.error(request, f"Phenotype Type {ptype} was NOT found in phenodb for {name}")
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
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            
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
        
        elif import_data_type == 'individual_ids':
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            
            for line in records:
                
                try:
                    centre = line['centre']
                    centre_id = line['centre_id']
                    new_centre_id = line['new_centre_id']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre centre_id new_centre_id'")
                    return 
            
                try:
                    source = Source.objects.get(source_name=centre)
                except Source.DoesNotExist:
                    messages.error(request, u"Can't find source in database '" + centre + u"'")
                    continue
            
                ## check if the id has already been entered for the given source
                try:
                    indId = IndividualIdentifier.objects.get(individual_string=centre_id,source_id=source.id)
                except IndividualIdentifier.DoesNotExist:
                    messages.error(request, u"Individual " + centre_id + u" NOT found in phenodb")
                    continue
                
                ## insert the new individual identifier
                newIndId = IndividualIdentifier()
                newIndId.individual = indId.individual
                newIndId.individual_string = new_centre_id
                newIndId.source = source
                newIndId.date_created = timezone.now()
                newIndId.last_updated = timezone.now()
                try:
                    newIndId.save()
                except IntegrityError:
                    print('not saved')
            
            return
            
        elif import_data_type == "samples":
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)

            for line in records:
                
                try:
                    centre = line['centre']
                    centre_id = line['centre_id']
                    sample_id = line['sample_id']
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre centre_id sample_id'")
                    return

                try:
                    helpers.add_sample(
                        centre=centre,
                        centre_id=centre_id,
                        sample_id=sample_id
                    )
                except Exception as e:
                    messages.error(request, e)

            return
        
        elif import_data_type == "add_sample_on_sample":
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
                
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
                newSample.date_created = timezone.now()
                newSample.last_updated = timezone.now()
                newSample.save()
            return
            
        elif import_data_type == "add_phenotype_values":
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            
            for line in records:
                
                try:
                    centre = line['centre']
                    centre_id = line['centre_id']
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'centre centre_id'")
                    return
                
                phenotypes = {}
                for col in line:
                    if col not in ['centre', 'centre_id']:
                        phenotypes[col] = line[col]

                try:
                    helpers.add_phenotype_values(
                        centre=centre,
                        centre_id=centre_id,
                        phenotypes=phenotypes
                    )
                except Exception as e:
                    messages.error(request, e)

            return
        
        elif import_data_type == "add_sample_feature_values":
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
            for line in records:
                try:
                    sample_id = line['sample_id']
                except KeyError:
                    messages.error(request, u"Input file is missing required column sample_id")
                    return

                sample_features = {}
                for col in line:
                    if col not in ['sample_id']:
                        sample_features[col] = line[col]
                
                try:
                    helpers.add_sample_features(
                        centre=centre,
                        centre_id=centre_id,
                        sample_id=sample_id,
                        sample_features=sample_features,
                    )
                except Exception as e:
                    messages.error(request, e)

            return
        
        elif import_data_type == "check_samples_in_warehouse":
            
            records = read_csv(request.FILES["file_to_import"], file_delimiter)
        
            for line in records:
                           
                try:
                    sample_id = line['sample_id']                    
                except KeyError:
                    messages.error(request, u"Input file is missing required column(s) 'sample_id'")
                    return     
    
                if Sample.objects.filter(sample_id=sample_id).exists(): 
                    continue
                else:
                    q = f"SELECT DISTINCT sanger_sample_id, supplier_name, cohort, country_of_origin, geographical_region  FROM samples WHERE name = '{sample_id}' ORDER BY checked_at desc;"
                    warehouseCursor.execute()
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
admin.site.register(SampleFeatureType)
admin.site.register(SampleFeature)


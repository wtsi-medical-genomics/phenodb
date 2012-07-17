from django import forms
from search.models import *
from django.contrib import admin
import datetime
from django.utils.timezone import utc
import csv
from django.db import connections
from decimal import *
from django.db import IntegrityError
from django.shortcuts import render
import sys

class BulkUploadForm(forms.ModelForm):
    file_to_import = forms.FileField()
    import_options = (
        ('Individuals','Individuals'),
        ('Phenotypes','Phenotypes'),
        ('Samples','Samples'),
        ('Sources','Sources')
    )
    import_data_type = forms.ChoiceField(import_options)

    class Meta:
        model = BulkUpload

class BulkUploadAdmin(admin.ModelAdmin):
    
    form = BulkUploadForm
    true_list = ["Yes", "yes", "true", "True", "1", "Affected", "affected"]
    false_list = ["No", "no", "false", "False", "0", '', "Unaffected", "unaffected"]
    
    #Overrides model object saving.
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def save_model(self, request, obj, form, change):
        records = csv.DictReader(request.FILES["file_to_import"])
        import_data_type = request.POST["import_data_type"]
        for line in records:
            if import_data_type == "Individuals":                
                ## required columns: Sample ID,Supplying Centre,Supplying centre sample ID,Sex,                
                try:
                    source = Source.objects.get(source_name=line['Supplying Centre'])
                except Source.DoesNotExist:
                    print u"Can't find source in database " + line['Supplying Centre']
                    continue
                
                ind = Individual()
                if self.is_number(line['Sex']):
                    ind.sex = line['Sex']
                else:
                    if line['Sex'] == "Female":
                        ind.sex = 2
                    elif line['Sex'] == "Male":
                        ind.sex = 1
                    else:
                        ind.sex = 0
                        
                ind.has_dup = False
                ind.flagged = False
                ind.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                ind.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                ind.save()                    
                                
                ## insert the individual identifier
                indId = IndividualIdentifier()
                indId.individual = ind
                indId.individual_string = line['Supplying centre sample ID']
                indId.source = source
                indId.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                indId.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)                
                try:
                    indId.save()
                except IntegrityError:
                    print u"Individual ID " + line['Supplying centre sample ID'] + " is already in the database"
                    continue
                                        
                ## insert phenotype values
                for col in line:                    
                    try:
                        pheno = Phenotype.objects.get(phenotype_name=col)
                    except Phenotype.DoesNotExist:
                        ## print u"Warning Can't find phenotype '" + col + "' in database"
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
                        affectVal.flagged = False
                        affectVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        affectVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            affectVal.save()
                        except:
                            print u"failed to save " + pheno.phenotype_name + u" " + line[col]           
                    elif pheno.phenotype_type.phenotype_type == u"Qualitative":
                        qualVal = QualitativePhenotypeValue()
                        qualVal.phenotype = pheno
                        qualVal.individual = ind
                        if line[col] == '':
                            continue
                        else:
                            qualVal.phenotype_value = line[col]
                        qualVal.flagged = False
                        qualVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        qualVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            qualVal.save()
                        except:
                            print u"failed to save " + pheno.phenotype_name + u" " + line[col]
                    elif pheno.phenotype_type.phenotype_type == u"Quantitative":
                        quantVal = QuantitiatvePhenotypeValue()
                        quantVal.phenotype = pheno
                        quantVal.individual = ind
                        if line[col] == '':
                            continue
                        elif line[col] == None:
                            continue
                        else:
                            quantVal.phenotype_value = Decimal(line[col])
                        quantVal.flagged = False
                        quantVal.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                        quantVal.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                        try:
                            quantVal.save()
                        except:
                            print u"failed to save " + pheno.phenotype_name + u" " + line[col]
                    else:
                        print u"unrecognised phenotype type " + pheno.phenotype_type.phenotype_type
                        
            elif import_data_type == "Phenotypes":
                ## required columns: Name,Type,Description
                try:
                    phenoType = PhenotypeType.objects.get(phenotype_type=line['Type'])
                except PhenotypeType.DoesNotExist:
                    print u"Phenotype Type " + line['Type'] + u" was NOT found in phenodb for " + line['Name']
                    continue
                         
                pheno = Phenotype()
                pheno.phenotype_name = line['Name']
                pheno.phenotype_type = phenoType
                pheno.phenotype_description = line['Description']
                try:
                    pheno.save()
                except IntegrityError:
                    print u"Phenotype " + line['Name'] + " is already in the database"
                    continue
                
            elif import_data_type == "Sources":
                ## required columns: Name,Contact,Description
                source = Source()
                source.source_name = line['Centre']
                source.contact_name = line['Contact']
                source.source_description = line['Description']
                try:
                    source.save()
                except IntegrityError:
                    print u"Source " + line['Centre'] + " is already in the database"
                    
            elif import_data_type == "Samples":
                ## required columns: Supplier_ID,Sample_ID
                try:
                    sampleIndId = IndividualIdentifier.objects.get(individual_string=line['Supplying centre sample ID'])
                except IndividualIdentifier.DoesNotExist:
                    print u"Individual " + line['Supplying centre sample ID'] + u" NOT found in phenodb"
                    continue
                          
                sample = Sample()
                sample.individual = sampleIndId.individual
                sample.sample_id = line['Sample ID']
                sample.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                sample.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                warehouseCursor = connections['warehouse'].cursor()
                warehouseCursor.execute("SELECT DISTINCT sanger_sample_id, supplier_name, gender FROM samples WHERE name = %s ORDER BY checked_at desc", sample.sample_id)
                row = warehouseCursor.fetchone()
                if row[0] is None:
                    print u"Sample " + sample.sample_id + u" NOT found in warehouse"
                else:
                    if row[1] == sampleIndId.individual_string:
                        sample.save()                        
                        if row[2] == sampleIndId.individual.sex:
                            print u"gender " + sampleIndId.individual.sex.str() + u" matches warehouse "  + row[2]
                        else:
                            print u"gender " + str(sampleIndId.individual.sex) + u" does not match warehouse "  + row[2]
                    else:
                        print u"supplier name " + str(sampleIndId.individual_string) + u" does not match warehouse "  + row[1]
                        
        ## return an array of messages that get printed to the browser                    
        return
                          
admin.site.register(Platform)
admin.site.register(PlatformType)
admin.site.register(PhenotypeType)
admin.site.register(Phenotype)
admin.site.register(Study)
admin.site.register(Source)
admin.site.register(QC)
admin.site.register(Individual)
admin.site.register(Sample)
admin.site.register(BulkUpload, BulkUploadAdmin)

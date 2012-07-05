from django import forms
from search.models import Platform
from search.models import PlatformType
from search.models import PhenotypeType
from search.models import Phenotype
from search.models import Study
from search.models import Source
from search.models import QC
from search.models import Sample
from search.models import Individual
from search.models import IndividualIdentifier
from search.models import BulkUpload
from django.contrib import admin
import datetime
from django.utils.timezone import utc
import csv

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
    
    #Mark other fields as read-only.
    form = BulkUploadForm
    
    #Overrides model object saving.
    def is_number(s):
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
                ## required columns: Gender,Centre,Supplier_ID
                ind = Individual()
                ## check if gender is a number otherwise try to convert
                ind.sex = 0
#               ind.sex = line['Gender']
                ind.has_dup = False
                ind.flagged = False
                ind.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                ind.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                ind.save()
                ## get the source id or die that the source is not recognised
                source = Source.objects.get(source_name='test')
#               source = Source.objects.get(source_name=line['Centre'])             
                indId = IndividualIdentifier()
                indId.individual = ind
                indId.individual_string = line['Supplier ID']
                indId.source = source
                indId.date_created = datetime.datetime.utcnow().replace(tzinfo=utc)
                indId.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)
                indId.save()
                
                ## loop through all the phenotypes
                pheno = Phenotype.objects.get(phenotype_name=i)
                
            elif import_data_type == "Phenotypes":
                ## required columns: Name,Type,Description
                phenoType = PhenotypeType.objects.get(phenotype_type=line['Type'])
                pheno = Phenotype()
                pheno.phenotype_name = line['Name']
                pheno.phenotype_type = phenoType
                pheno.phenotype_description = line['Description']
                pheno.save()
            elif import_data_type == "Sources":
                ## required columns: Name,Contact,Description
                source = Source()
                source.source_name = line['Centre']
                source.contact_name = line['Contact']
                source.source_description = line['Description']
                source.save()
            elif import_data_type == "Samples":
                print "inserting samples"
            else:
                print "else"
                
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

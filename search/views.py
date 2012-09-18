from django.template import RequestContext
from django.shortcuts import render, render_to_response
from search.models import IndividualIdentifier, Phenotype, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample, Platform, Study, QC
from django import forms
import django_tables2 as tables
from django_tables2 import RequestConfig
import csv
from django.http import HttpResponse

class SearchForm(forms.Form):
    id_textarea = forms.CharField(widget=forms.Textarea)
    phenotypes = forms.ModelMultipleChoiceField(queryset=Phenotype.objects.all(), required=False)

class QueryTable(tables.Table):    
    identifier = tables.Column()
    value = tables.Column()
    
    class Meta:        
        attrs = {'class': 'table table-striped table-bordered'}

class IndividualTable(tables.Table):
    individual_id = tables.Column()
    sex = tables.Column()
    source = tables.Column()
    samples = tables.Column()
    phenotype_values = tables.Column()
    
    class Meta:
        attrs = {'class': 'table table-striped table-bordered'}

class PhenotypeTable(tables.Table):        
    class Meta:
        model = Phenotype
        fields = ('phenotype_name', 'phenotype_description')
        attrs = {'class': 'table table-striped table-bordered'}

class PlatformTable(tables.Table):        
    class Meta:
        model = Platform
        fields = ('platform_name', 'platform_type', 'platform_description')
        attrs = {'class': 'table table-striped table-bordered'}

class StudyTable(tables.Table):        
    class Meta:
        model = Study
        fields = ('study_name', 'study_name', 'data_location', 'study_description')         
        attrs = {'class': 'table table-striped table-bordered'}
        
class QCTable(tables.Table):        
    class Meta:
        model = QC
        fields = ('qc_name', 'qc_description')         
        attrs = {'class': 'table table-striped table-bordered'}
    
def home(request):
    return render(request, 'search/home.html', {})

def showPhenotypes(request):
    table = PhenotypeTable(Phenotype.objects.all())
    return render_to_response('search/dataview.html', {'table': table}, context_instance=RequestContext(request))

def showPlatforms(request):
    table = PlatformTable(Platform.objects.all())
    return render_to_response('search/dataview.html', {'table': table}, context_instance=RequestContext(request))

def showStudies(request):
    table = StudyTable(Study.objects.all())
    return render_to_response('search/dataview.html', {'table': table}, context_instance=RequestContext(request))

def showQCs(request):
    table = QCTable(QC.objects.all())
    return render_to_response('search/dataview.html', {'table': table}, context_instance=RequestContext(request))

def idSearch(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid(): # All validation rules pass
            
            textarea_values = form.cleaned_data['id_textarea'].splitlines()
            
            selected_phenotypes = form.cleaned_data['phenotypes']
            
            ## for each id
            inds = []
            for line in textarea_values:
                query_id = line.strip()
                query_results = IndividualIdentifier.objects.filter(individual_string=query_id)                
                if query_results.count() > 0:                                                
                    for ind in query_results:
                        samples = []
                        for sample in Sample.objects.filter(individual=ind):
                            samples.append(sample.sample_id)
                        
                        ## for each of the phenotypes get the individual value
                        phenotype_values = []
#                        for phenotype in selected_phenotypes:                            
#                            phenotype_obj = Phenotype.objects.get(phenotype_name=phenotype)
#                            phenotype_type = phenotype_obj.phenotype_type.phenotype_type
#                            print phenotype
#                            print phenotype_obj.id
#                            print ind.individual_id
#                            if phenotype_type == 'Affection Status':
#                                affection_status = AffectionStatusPhenotypeValue.objects.filter(phenotype_id=phenotype_obj.id,individual_id=ind.individual_id)
#                                if affection_status.count() > 0:
#                                    phenotype_values.append(affection_status.phenotype_value)
#                            if phenotype_type == 'Qualitative':
#                                qualitative = QualitativePhenotypeValue.objects.filter(phenotype_id=phenotype_obj.id,individual_id=ind.individual_id)
#                                if qualitative.count() > 0:
#                                    phenotype_values.append(qualitative.phenotype_value)
#                            if phenotype_type == 'Quantitative':
#                                quantitative = QuantitiatvePhenotypeValue.objects.filter(phenotype_id=phenotype_obj.id,individual_id=ind.individual_id)
#                                if quantitative.count() > 0:
#                                    phenotype_values.append(quantitative.phenotype_value)
                            ## phenotype type not known
                            
                        
                        ## deafult columns
                        ind_results = {'individual_id':ind.individual_string,
                                       'sex':ind.individual.sex,
                                       'source':ind.source.source_name,
                                       'samples':samples,
                                       'phenotype_values':phenotype_values
                                       }
                                            
                        
#                        affection_results = AffectionStatusPhenotypeValue.objects.filter(individual=ind)                     
#                        qualitative_results = QualitativePhenotypeValue.objects.filter(individual=ind)                    
#                        quantitiative_results = QuantitiatvePhenotypeValue.objects.filter(individual=ind)
                        
                        inds.append(ind_results)
            table = IndividualTable(inds)
            return render_to_response('search/idresults.html', {'table': table}, context_instance=RequestContext(request))
#            else:
#            id not found

    else:
        form = SearchForm() # An unbound form
        return render(request, 'search/idsearch.html', {'form': form,})

def querybuilder(request):
    if request.method == 'POST':
        print request.POST
        
        ## becuase we are not using a django form we need to check the form data is valid ourselves 
        select = request.POST['select']            
        table = request.POST['from']
        where = request.POST['where']
        where_is = request.POST['is']
        querystr = request.POST['querystr'].strip()
        
        ## go through a loop of all the queries the user has created
        ## for every query after the first use the list of query results to perform the next query        
            
        if table == 'phenotype':
            ## get the phenotype object
            phenotype = Phenotype.objects.get(id=where)            
            if phenotype.phenotype_type.phenotype_type == 'Affection Status':
                if where_is == 'eq':
                    result_set = AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=querystr)
                else:
                    print "ERROR: not a valid comparison for an affection status field"
                        
            elif phenotype.phenotype_type.phenotype_type == 'Qualitative':
                if where_is == 'eq':
                    result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr)
                elif where_is == 'contains':
                    result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__icontains=querystr)
                elif where_is == 'starts_with':
                    result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__istartswith=querystr)
                elif where_is == 'ends_with':
                    result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iendswith=querystr)
                else:
                    print "ERROR: not a valid comparison for an Qualitative field"
                                                            
            elif phenotype.phenotype_type.phenotype_type == 'Quantitative':
                if where_is == 'eq':
                    result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr)
                elif where_is == 'gt':
                    result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gt=querystr)
                elif where_is == 'gte':
                    result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gte=querystr)
                elif where_is == 'lt':
                    result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lt=querystr)
                elif where_is == 'lte':
                    result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lte=querystr)
                else:
                    print "ERROR: not a valid comparison for an Quantitiatve field"
            
        if result_set.count() > 0:
            ## save all the results in a dict matching the table class
            query_results = []
            for result in result_set:
                query_results.append({'identifier':result.individual.id,'value':result.phenotype_value})         
                table = QueryTable(query_results)
            return render_to_response('search/queryresults.html', {'table': table, 'count': result_set.count()}, context_instance=RequestContext(request))
        else:
            # return to the form with a message that no results were found
            return render_to_response('search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':"Sorry your query didn't return any results, please try another query."}, context_instance=RequestContext(request))
    else:
        # pass all the phenotypes/platforms/studies etc to the form                 
        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all()})

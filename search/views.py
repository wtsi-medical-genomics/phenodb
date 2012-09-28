from django.template import RequestContext
from django.shortcuts import render, render_to_response
from search.models import IndividualIdentifier, Phenotype, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample, Platform, Study, QC
from django import forms

import sys
sys.path.append('/nfs/users/nfs_j/jm20/python_modules/lib/python2.6/site-packages')

import django_tables2 as tables
from django_tables2 import RequestConfig
import csv
from django.http import HttpResponse
from time import time
from django.core import serializers

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
#    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    return render(request, 'search/dataview.html', {'table': table})

def showPlatforms(request):
    table = PlatformTable(Platform.objects.all())
#    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    return render(request, 'search/dataview.html', {'table': table})

def showStudies(request):
    table = StudyTable(Study.objects.all())
#    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    return render(request, 'search/dataview.html', {'table': table})

def showQCs(request):
    table = QCTable(QC.objects.all())
#    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    return render(request, 'search/dataview.html', {'table': table})

def all_json_models(request, menuid):
    print menuid
    if menuid == 'phenotype':
        menuitems = Phenotype.objects.all()
    elif menuid == 'platform':
        menuitems = Platform.objects.all()
    elif menuid == 'study':
        menuitems = Study.objects.all()
    elif menuid == 'qc':
        menuitems = QC.objects.all()
    json_models = serializers.serialize("json", menuitems)
    return HttpResponse(json_models, mimetype="application/javascript")

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
            return render(request, 'search/idresults.html', {'table': table})
#            else:
#            id not found

    else:
        form = SearchForm() # An unbound form
        return render(request, 'search/idsearch.html', {'form': form,})

def querybuilder(request):
    if request.method == 'POST':
        print request.POST
        start_time = time()
        ## becuase we are not using a django form we need to check the form data is valid ourselves 
        select = request.POST['select']            
        tables = request.POST.getlist('from')
        wheres = request.POST.getlist('where')
        where_iss = request.POST.getlist('is')
        querystrs = request.POST.getlist('querystr')         
                
        ## perform the first query:        
        table = tables.pop()        
        where = wheres.pop()
        where_is = where_iss.pop()
        querystr = querystrs.pop().strip()
        query_results, query_lookup = query_db(select, table, where, where_is, querystr)
        
        ## if there are more queries then perform them on the ids returned from the first query
        while len(tables) > 0:
            table = tables.pop()
            where = wheres.pop()
            where_is = where_iss.pop()
            querystr = querystrs.pop().strip()
            query_results, query_lookup = query_db_with_ids(select, table, where, where_is, querystr, query_lookup)        
        
        ## no more queries so return the data if there is any
        if len(query_results) > 0:
            table = QueryTable(query_results)
#            RequestConfig(request, paginate={"per_page": 50}).configure(table)
            query_time = time() - start_time
            return render(request, 'search/queryresults.html', {'table': table, 'count':len(query_results),'querytime':query_time})
        else:
            message = "Sorry your query didn't return any results, please try another query."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})  
            
    else:
        # pass all the phenotypes/platforms/studies etc to the form                 
        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all()})
    
def query_db (select, table, where, where_is, querystr):
    
    query_results_table = []
    query_results_lookup = {}
    
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
          
        print "query done"
                        
        if result_set.count() > 0:            
            ## save all the results in a dict matching the results table class
            for result in result_set:
                query_results_table.append({'identifier':result.individual.id,'value':result.phenotype_value}) 
                query_results_lookup[result.individual.id] = result.phenotype_value
        
        print "processing done"
                
    return query_results_table, query_results_lookup

def query_db_with_ids(select, table, where, where_is, querystr, query_lookup):
    
    new_query_results = []
    query_results_lookup = {}
    
    if table == 'phenotype':
        ## get the phenotype object
        phenotype = Phenotype.objects.get(id=where)            
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            if where_is == 'eq':
                new_result_set = AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=querystr)
            else:
                print "ERROR: not a valid comparison for an affection status field"
                        
        elif phenotype.phenotype_type.phenotype_type == 'Qualitative':
            if where_is == 'eq':
                new_result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr)
            elif where_is == 'contains':
                new_result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__icontains=querystr)
            elif where_is == 'starts_with':
                new_result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__istartswith=querystr)
            elif where_is == 'ends_with':
                new_result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iendswith=querystr)
            else:
                print "ERROR: not a valid comparison for an Qualitative field"
                                                            
        elif phenotype.phenotype_type.phenotype_type == 'Quantitative':
            if where_is == 'eq':
                new_result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr)
            elif where_is == 'gt':
                new_result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gt=querystr)
            elif where_is == 'gte':
                new_result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gte=querystr)
            elif where_is == 'lt':
                new_result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lt=querystr)
            elif where_is == 'lte':
                new_result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lte=querystr)
            else:
                print "ERROR: not a valid comparison for an Quantitiatve field"        
        
        if new_result_set.count() > 0:
            for result in new_result_set:
                if result.individual.id in query_lookup:
                    new_query_results.append({'identifier':result.individual.id,'value':[result.phenotype_value,query_lookup[result.individual.id]]})
                    query_results_lookup[result.individual.id] = [result.phenotype_value,query_lookup[result.individual.id]]

    return new_query_results, query_results_lookup

from django.template import RequestContext
from django.shortcuts import render, render_to_response
from search.models import IndividualIdentifier, Phenotype, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample, Platform, Study, QC, Individual
from django import forms
import django_tables2 as tables
from django_tables2 import RequestConfig
import csv
from django.http import HttpResponse
from time import time
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class SearchForm(forms.Form):
    id_textarea = forms.CharField(widget=forms.Textarea)
    phenotypes = forms.ModelMultipleChoiceField(queryset=Phenotype.objects.all(), required=False)

class QueryTable(tables.Table):    
    identifier = tables.Column()
    
    class Meta:        
        attrs = {'class': 'table table-striped table-bordered'}

class IndividualTable(tables.Table):
    model = Individual
    
    class Meta:
        fields = ('id', 'sex')
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
    return render(request, 'search/dataview.html', {'table': table})

def showPlatforms(request):
    table = PlatformTable(Platform.objects.all())
    return render(request, 'search/dataview.html', {'table': table})

def showStudies(request):
    table = StudyTable(Study.objects.all())
    return render(request, 'search/dataview.html', {'table': table})

def showQCs(request):
    table = QCTable(QC.objects.all())
    return render(request, 'search/dataview.html', {'table': table})

def showIndividual(request, ind_id):
    queryresult = IndividualIdentifier.objects.get(individual_string=ind_id)
    ## fill up the table info
    table_info = {}
    table = IndividualTable(table_info)
    return render(request, 'search/dataview.html', {'table': table})

def all_json_models(request, menuid):
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
        start_time = time()
        
        results_per_page = 25     # default value
                
        select = request.POST['select']            
        tables = request.POST.getlist('from')
        wheres = request.POST.getlist('where')
        where_iss = request.POST.getlist('is')
        querystrs = request.POST.getlist('querystr')
        
        ## check that all the queries contain something for each field (each element of each list is true)
        if (all(querystrs) & all(where_iss) & all(wheres) & all(tables)):
            tables_string = "_".join(tables)
            wheres_string = "_".join(wheres)
            where_iss_string = "_".join(where_iss)
            querystr_string = "_".join(querystrs)
                
            ## perform the first query:        
            table = tables.pop()        
            where = wheres.pop()
            where_is = where_iss.pop()
            querystr = querystrs.pop().strip()
            query_results = query_db(select, table, where, where_is, querystr)
        
            ## record the query to print on the results page
        
            query_summary = ["FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr]
        
            ## if there are more queries then perform them on the ids returned from the first query
            while len(tables) > 0:
                table = tables.pop()
                where = wheres.pop()
                where_is = where_iss.pop()
                querystr = querystrs.pop().strip()
                query_results = query_db_with_ids(select, table, where, where_is, querystr, query_results)
            
                query_summary.append("+ FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr)
        
            ## no more queries so return the data if there is any
            if len(query_results) > 0:
            
                paginator = parse_query_results(query_results, results_per_page)
                        
                page = request.GET.get('page')
                try:
                    page_results = paginator.page(page)
                except PageNotAnInteger:
                    # If page is not an integer, deliver first page.
                    page_results = paginator.page(1)
                except EmptyPage:
                    # If page is out of range (e.g. 9999), deliver last page of results.
                    page_results = paginator.page(paginator.num_pages)
                                    
                table = QueryTable(page_results)            
                query_time = time() - start_time
                return render(request, 'search/queryresults.html', {'table': table, 
                                                                    'count':len(query_results),
                                                                    'querytime':query_time, 
                                                                    'page_results':page_results, 
                                                                    'select':select, 
                                                                    'tables_str':tables_string, 
                                                                    'where_str':wheres_string, 
                                                                    'whereis_str':where_iss_string,
                                                                    'querystr_str':querystr_string,
                                                                    'query_summary':query_summary,
                                                                    'results_per_page':results_per_page})
            else:
                message = "Sorry your query didn't return any results, please try another query."
                return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
        else:
            message = "Query form contains missing information, please complete all fields and try again."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
    else:
        # pass all the phenotypes/platforms/studies etc to the form                 
        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all()})
        
def querypage(request, page, results_per_page, select, tables_str, where_str, whereis_str, querystr_str):
    start_time = time()
    ## split the strings containing multiple values
    table_list = tables_str.split("_")
    where_list = where_str.split("_")
    whereis_list = whereis_str.split("_")
    querystr_list = querystr_str.split("_")
    
    ## perform the first query:        
    table = table_list.pop()        
    where = where_list.pop()
    where_is = whereis_list.pop()
    querystr = querystr_list.pop().strip()
    query_results = query_db(select, table, where, where_is, querystr)
    
    ## record the query to print on the results page
    query_summary = ["FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr]
        
    ## if there are more queries then perform them on the ids returned from the first query
    while len(table_list) > 0:
        table = table_list.pop()        
        where = where_list.pop()
        where_is = whereis_list.pop()
        querystr = querystr_list.pop().strip()
        query_results = query_db_with_ids(select, table, where, where_is, querystr, query_results)        

        query_summary.append("+ FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr)

    paginator = parse_query_results(query_results, results_per_page)
    
    try:
        page_results = paginator.page(page)
    except EmptyPage:
        page_results = paginator.page(paginator.num_pages)
            
    table = QueryTable(page_results)
            
    query_time = time() - start_time
    
    return render(request, 'search/queryresults.html', {'table': table, 
                                                        'count':len(query_results),
                                                        'querytime':query_time, 
                                                        'page_results':page_results, 
                                                        'select':select, 
                                                        'tables_str':tables_str, 
                                                        'where_str':where_str, 
                                                        'whereis_str':whereis_str,
                                                        'querystr_str':querystr_str,
                                                        'query_summary':query_summary,
                                                        'results_per_page':results_per_page})
    
def query_export(request, select, tables_str, where_str, whereis_str, querystr_str):
    ## split the strings containing multiple values
    table_list = tables_str.split("_")
    where_list = where_str.split("_")
    whereis_list = whereis_str.split("_")
    querystr_list = querystr_str.split("_")
    
    ## perform the first query:        
    table = table_list.pop()        
    where = where_list.pop()
    where_is = whereis_list.pop()
    querystr = querystr_list.pop().strip()
    query_results = query_db(select, table, where, where_is, querystr)
        
    ## if there are more queries then perform them on the ids returned from the first query
    while len(table_list) > 0:
        table = table_list.pop()        
        where = where_list.pop()
        where_is = whereis_list.pop()
        querystr = querystr_list.pop().strip()
        query_results = query_db_with_ids(select, table, where, where_is, querystr, query_results)        
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
    
    writer = csv.writer(response)

    for e in query_results:
        writer.writerow(e)    
    
    return response
    
def query_db (select, table, where, where_is, querystr):
    
    if table == 'phenotype':
        ## get the phenotype object
        phenotype = Phenotype.objects.get(id=where)            
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            ## the user should only be offered the equals option for this type of phenotype
            if where_is == 'eq':
                return AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=querystr).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for an affection status field"
                return None                
                        
        elif phenotype.phenotype_type.phenotype_type == 'Qualitative':
            if where_is == 'eq':
                return QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr).values_list('individual_id')
            elif where_is == 'contains':
                return QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__icontains=querystr).values_list('individual_id')
            elif where_is == 'starts_with':
                return QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__istartswith=querystr).values_list('individual_id')
            elif where_is == 'ends_with':
                return QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iendswith=querystr).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for a Qualitative field"
                return None
                                                            
        elif phenotype.phenotype_type.phenotype_type == 'Quantitative':
            if where_is == 'eq':
                return QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr).values_list('individual_id')
            elif where_is == 'gt':
                return QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gt=querystr).values_list('individual_id')
            elif where_is == 'gte':
                return QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gte=querystr).values_list('individual_id')
            elif where_is == 'lt':
                return QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lt=querystr).values_list('individual_id')
            elif where_is == 'lte':
                return QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lte=querystr).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for a Quantitiatve field"
                return None
    else:
        print "Search table not currently supported"
        return None     
         

def query_db_with_ids(select, table, where, where_is, querystr, last_query):
    
    if table == 'phenotype':
        phenotype = Phenotype.objects.get(id=where)            
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            if where_is == 'eq':
                result_set = AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=querystr).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for an affection status field"
                        
        elif phenotype.phenotype_type.phenotype_type == 'Qualitative':
            if where_is == 'eq':
                result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr).values_list('individual_id')
            elif where_is == 'contains':
                result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__icontains=querystr).values_list('individual_id')
            elif where_is == 'starts_with':
                result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__istartswith=querystr).values_list('individual_id')
            elif where_is == 'ends_with':
                result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iendswith=querystr).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for a Qualitative field"
                                                            
        elif phenotype.phenotype_type.phenotype_type == 'Quantitative':
            if where_is == 'eq':
                result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__iexact=querystr).values_list('individual_id')
            elif where_is == 'gt':
                result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gt=querystr).values_list('individual_id')
            elif where_is == 'gte':
                result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__gte=querystr).values_list('individual_id')
            elif where_is == 'lt':
                result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lt=querystr).values_list('individual_id')
            elif where_is == 'lte':
                result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__lte=querystr).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for a Quantitiatve field"        
        
        if result_set.count() > 0:
            print "queryset size " + str(result_set.count())
            intersection_set = set(list(last_query)).intersection(set(list(result_set)))
            return list(intersection_set)
        else:
            print "ERROR: no results found"
            return None
                        
    else:
        print "ERROR: Search table not currently supported"
        return None

def parse_query_results(query_results, results_per_page):
    
    ## query results is a list of individual ids tuples
    ## from the intersection of all queries
    query_result_ids = []
    for e in query_results:
        query_result_ids.append(e[0])
#        query_result_ids.append({'identifier': e[0]})                
            
    ## get a dict of all the ids and their objects
    bulk_query_results = Individual.objects.in_bulk(query_result_ids)
            
    ## put all of the objects into a list
    query_result_objs = []
    for key in bulk_query_results:    
        ind = bulk_query_results[key]
        ## enter a link to an individual view
        query_result_objs.append({'identifier':ind.id})
            
    return Paginator(query_result_objs, results_per_page)

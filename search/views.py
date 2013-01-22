from django.template import RequestContext
from django.shortcuts import render, render_to_response
from search.models import *
from django import forms
import django_tables2 as tables
from django_tables2 import RequestConfig
import csv
from django.http import HttpResponse
from time import time
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json


class PhenotypeTable(tables.Table):        
    class Meta:
        model = Phenotype
        fields = ('phenotype_name', 'phenotype_description', 'phenotype_type')
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
        
class SourceTable(tables.Table):        
    class Meta:
        model = Source
        fields = ('source_name', 'contact_name', 'source_description')         
        attrs = {'class': 'table table-striped table-bordered'}

class IndividualTable(tables.Table):        
    class Meta:
        model = Individual
        fields = ('id', 'sex')         
        attrs = {'class': 'table table-striped table-bordered'}
        
class SampleTable(tables.Table):        
    class Meta:
        model = Sample
        fields = ('sample_id')         
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

def showSources(request):
    table = SourceTable(Source.objects.all())
    return render(request, 'search/dataview.html', {'table': table})

def showIndividuals(request):
    table = IndividualTable(Individual.objects.all())
    return render(request, 'search/dataview.html', {'table': table})

def showSamples(request):
    table = SampleTable(Sample.objects.all())
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

def all_search_options(request, menuid):
    phenotype = Phenotype.objects.get(id=menuid)            
    menuitems = []
    if phenotype.phenotype_type.phenotype_type == 'Affection Status':
        menuitems.append({"value": "true", "text": "True" })
        menuitems.append({"value": "false", "text": "False"})
        menuitems.append({"value": "isnull", "text": "Is NULL"})
        menuitems.append({"value": "notnull", "text": "Is not NULL"})
    elif phenotype.phenotype_type.phenotype_type == 'Qualitative':        
        menuitems.append({"value": "eq", "text": "Equals" })
        menuitems.append({"value": "contains", "text": "Contains" })
        menuitems.append({"value": "starts_with", "text": "Starts with" })
        menuitems.append({"value": "ends_with", "text": "Ends with" })
        menuitems.append({"value": "isnull", "text": "Is NULL"})
        menuitems.append({"value": "notnull", "text": "Is not NULL"})        
    elif phenotype.phenotype_type.phenotype_type == 'Quantitative':        
        menuitems.append({"value": "eq", "text": "==" })
        menuitems.append({"value": "gt", "text": ">" })
        menuitems.append({"value": "gte", "text": ">=" })
        menuitems.append({"value": "lt", "text": "<" })
        menuitems.append({"value": "lte", "text": "<=" })
        menuitems.append({"value": "isnull", "text": "Is NULL"})
        menuitems.append({"value": "notnull", "text": "Is not NULL"})
    return HttpResponse(json.dumps(menuitems), mimetype="application/javascript")

def generate_query_results_table(output, query_results):
    
    table_html = "<table class=\"table table-striped table-bordered\">\n"
    
    for column in output:
        table_html = "".join((table_html, "<th>"+ column +"</th>\n"))

    for results_row in query_results:

        table_html = "".join((table_html, "<tr>\n"))

        for value in results_row:
            table_html = "".join((table_html, "<td>" + value + "</td>\n"))

        table_html = "".join((table_html, "</tr>\n"))

    return "".join((table_html, "</table>\n"))

def querybuilder(request):
    if request.method == 'POST':
        start_time = time()        
        results_per_page = 25     # default value
        tables    = request.POST.getlist('from')
        wheres    = request.POST.getlist('where')
        where_iss = request.POST.getlist('is')
        querystrs = request.POST.getlist('querystr')        
        search_in = request.POST['searchIn']        
        output    = request.POST.getlist('output')
        
        ## check that all the queries contain something for each required field (each element of each list is true)
        if (all(where_iss) & all(wheres) & all(tables)):
            tables_string    = "_".join(tables)
            wheres_string    = "_".join(wheres)
            where_iss_string = "_".join(where_iss)
            querystr_string  = "_".join(querystrs)
            output_string    = "_".join(output)
            
            ## search all records or from a list of individuals
            if (search_in == 'userlist'):
                
                query_ids = []
                
                if (request.POST['individual_list']):
                    textarea_values = request.POST['individual_list'].splitlines()
                    for line in textarea_values:
                        if (line.strip()):
                            query_ids.append(line.strip())
                                                
                elif (request.FILES['individual_file']):
                    indFile = request.FILES['individual_file']                    
                    if not indFile.multiple_chunks():
                        file_lines = indFile.read().splitlines()                        
                        for line in file_lines:
                            if (line.strip()):
                                query_ids.append(line.strip())                         
                    else:
                        message = "Sorry your file '" + indFile.name + "' is too large to read into memory."
                        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})                    
                                
                if (len(query_ids) > 0):                    
                    # array of tuples
                    db_ids = []                
                    for ind_id in query_ids:                                                
                        query_result = IndividualIdentifier.objects.filter(individual_string=ind_id).values_list('individual_id')                        
                        if (len(query_result) > 0):
                            # append just the first tuple of the list
                            db_ids.append(query_result[0])
                                                        
                    if (len(db_ids) > 0):
                        
                        print len(db_ids)
                        
                        results = perform_queries_with_ids(request, tables, wheres, where_iss, querystrs, db_ids)
                        result_ids = results[0]
                        query_summary = results[1]
                        
                        print len(result_ids)
                        
                        ## no more queries so return the data if there is any
                        if len(result_ids) > 0:
                    
                            query_ids_objs = parse_query_results(result_ids)
                    
                            paginator = Paginator(query_ids_objs, results_per_page)
                    
                            page = request.GET.get('page')
                            try:
                                page_results = paginator.page(page)
                            except PageNotAnInteger:
                                # If page is not an integer, deliver first page.
                                page_results = paginator.page(1)
                            except EmptyPage:
                                # If page is out of range (e.g. 9999), deliver last page of results.
                                page_results = paginator.page(paginator.num_pages)
                    
                            table_html = generate_query_results_table(output, get_output_data(page_results, output))
                            query_time = time() - start_time
                            return render(request, 'search/queryresults.html', {'tablehtml': table_html,
                                                                                'output_str': output_string, 
                                                                                'count':len(query_ids),
                                                                                'querytime':query_time, 
                                                                                'page_results':page_results,                                                                         
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
                        message = "Sorry none of the individual IDs you provided could be found, please try again."
                        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                
                else:
                    message = "No individual IDs were input, please try again."
                    return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                
                ## allow the users to just supply the list of inds and a null filter
                
            ## else search all records - as before                
            elif (search_in ==  'all'):
                
                query_results = perform_queries(request, tables, wheres, where_iss, querystrs)
                query_ids = query_results[0]
                query_summary = query_results[1] 
                
                ## no more queries so return the data if there is any
                if len(query_ids) > 0:
                    
                    query_ids_objs = parse_query_results(query_ids)
                    
                    paginator = Paginator(query_ids_objs, results_per_page)
                    
                    page = request.GET.get('page')
                    try:
                        page_results = paginator.page(page)
                    except PageNotAnInteger:
                        # If page is not an integer, deliver first page.
                        page_results = paginator.page(1)
                    except EmptyPage:
                        # If page is out of range (e.g. 9999), deliver last page of results.
                        page_results = paginator.page(paginator.num_pages)
                    
                    table_html = generate_query_results_table(output, get_output_data(page_results, output))
                    query_time = time() - start_time
                    return render(request, 'search/queryresults.html', {'tablehtml': table_html,
                                                                        'output_str': output_string, 
                                                                        'count':len(query_ids),
                                                                        'querytime':query_time, 
                                                                        'page_results':page_results,                                                                         
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
        
def querypage(request, page, results_per_page, tables_str, where_str, whereis_str, querystr_str, output_str):
    start_time = time()
    ## split the strings containing multiple values
    tables = tables_str.split("_")
    wheres = where_str.split("_")
    where_iss = whereis_str.split("_")
    querystrs = querystr_str.split("_")
    output = output_str.split("_")
    
    query_results = perform_queries(request, tables, wheres, where_iss, querystrs)
    query_ids = query_results[0]
    query_summary = query_results[1]

    query_ids_objs = parse_query_results(query_ids)
    paginator = Paginator(query_ids_objs, results_per_page)
    
    try:
        page_results = paginator.page(page)
    except EmptyPage:
        page_results = paginator.page(paginator.num_pages)
            
    table_html = generate_query_results_table(output, get_output_data(page_results, output))
            
    query_time = time() - start_time
    
    return render(request, 'search/queryresults.html', {'tablehtml': table_html, 
                                                        'output_str': output_str,
                                                        'count':len(query_ids),
                                                        'querytime':query_time, 
                                                        'page_results':page_results,                                                         
                                                        'tables_str':tables_str, 
                                                        'where_str':where_str, 
                                                        'whereis_str':whereis_str,
                                                        'querystr_str':querystr_str,
                                                        'query_summary':query_summary,
                                                        'results_per_page':results_per_page})
    
def query_export(request, tables_str, where_str, whereis_str, querystr_str, output_str):
    ## split the strings containing multiple values
    tables = tables_str.split("_")
    wheres = where_str.split("_")
    where_iss = whereis_str.split("_")
    querystrs = querystr_str.split("_")
    output = output_str.split("_")
    
    query_results = perform_queries(request, tables, wheres, where_iss, querystrs)
    query_ids = query_results[0]
    query_ids_objs = parse_query_results(query_ids)
    parsed_results = get_output_data(query_ids_objs, output)
        
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    
    writer = csv.writer(response)

    for e in parsed_results:
        writer.writerow(e)    
    
    return response
    
def query_db (table, where, where_is, querystr):
    
    if table == 'phenotype':
        ## get the phenotype object
        phenotype = Phenotype.objects.get(id=where)            
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            ## the user should only be offered the equals option for this type of phenotype
            if where_is == 'true':
                return AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=1).values_list('individual_id')
            elif where_is == 'false':
                return AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=0).values_list('individual_id')
            elif where_is == 'notnull':
                return AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=False).values_list('individual_id')
            elif where_is == 'isnull':
                return AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=True).values_list('individual_id')
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
            elif where_is == 'isnull':
                return QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=True).values_list('individual_id')
            elif where_is == 'notnull':
                return QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=False).values_list('individual_id')
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
            elif where_is == 'isnull':
                return QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=True).values_list('individual_id')
            elif where_is == 'notnull':
                return QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=False).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for a Quantitiatve field"
                return None
    else:
        print "Search table not currently supported"
        return None     
         

def query_db_with_ids(table, where, where_is, querystr, last_query):
    
    if table == 'phenotype':
        phenotype = Phenotype.objects.get(id=where)            
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            if where_is == 'true':
                return AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=1).values_list('individual_id')
            elif where_is == 'false':
                return AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=0).values_list('individual_id')
            elif where_is == 'notnull':
                result_set = AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=False).values_list('individual_id')
            elif where_is == 'isnull':
                result_set = AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=True).values_list('individual_id')
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
            elif where_is == 'isnull':
                result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=True).values_list('individual_id')
            elif where_is == 'notnull':
                result_set = QualitativePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=False).values_list('individual_id')
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
            elif where_is == 'isnull':
                result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=True).values_list('individual_id')
            elif where_is == 'notnull':
                result_set = QuantitiatvePhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=False).values_list('individual_id')
            else:
                print "ERROR: not a valid comparison for a Quantitiatve field"        
        if result_set.count() > 0:
            intersection_set = set(list(last_query)).intersection(set(list(result_set)))
            return list(intersection_set)
        else:
            print "ERROR: no results found"
            return None
                        
    else:
        print "ERROR: Search table not currently supported"
        return None

def parse_query_results(query_results):
    
    ## query results is a list of individual ids tuples
    ## from the intersection of all queries
    query_result_ids = []
    for e in query_results:
        query_result_ids.append(e[0])
            
    ## get a dict of all the ids and their objects
    bulk_query_results = Individual.objects.in_bulk(query_result_ids)
            
    ## put all of the objects into a list
    query_result_objs = []
    for key in bulk_query_results:    
        ind = bulk_query_results[key]
        ## enter a link to an individual view
        query_result_objs.append({'identifier':ind.id})
            
    return query_result_objs

def get_output_data(page_results, output_columns):
    
    ## page_results is a list of individual ids tuples
    ## from the intersection of all queries
    ## get the result columns that user wants
    parsed_results = []
    for indId in page_results:
        row_values = []
        for column in output_columns:
            if column == 'IndividualID':                
                indStr = IndividualIdentifier.objects.filter(individual_id = indId['identifier']).values('individual_string')                            
                ## if there are more than 1 id then join the strings
                row_values.append(indStr[0]['individual_string'])
            elif column == 'Source':
                indObject = IndividualIdentifier.objects.filter(individual_id = indId['identifier'])
                source = indObject[0].source.source_name                                
                row_values.append(source)
            elif column == 'Sex':
                indObject = IndividualIdentifier.objects.filter(individual_id = indId['identifier'])
                sex = indObject[0].individual.sex
                if (sex == 1):
                    row_values.append("Male")
                elif (sex == 2):
                    row_values.append("Female")
                else:
                    row_values.append("Unkown")
            elif column == 'SampleIDs':
                sampleId = Sample.objects.filter(individual_id = indId['identifier']).values('sample_id')
                if len(sampleId) > 0:
                    row_values.append(sampleId[0]['sample_id'])
#            elif column == 'Study':
#                studysample = StudySamples.objects.filter(individual_id = indId['identifier'])
#                
#                for study in studysample:
#                    row_values.append(study.study.study_name)
#            elif column == 'Platform':
#                
#            elif column == 'QC': 
            
        parsed_results.append(row_values)
    
    return parsed_results
    
def perform_queries(request, tables, wheres, where_iss, querystrs):
    ## perform the first query:        
    table = tables.pop()        
    where = wheres.pop()
    where_is = where_iss.pop()                
                
    phenotype = Phenotype.objects.get(id=where)
    phenotype_type = phenotype.phenotype_type.phenotype_type
                                            
    if phenotype_type == 'Affection Status':
        querystr = ''
    else:
        querystr = querystrs.pop().strip()
                    
    query_results = query_db(table, where, where_is, querystr)
    
    print query_results
                
    query_summary = ["FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr]
        
    ## if there are more queries then perform them on the ids returned from the first query
    while len(tables) > 0:
        table = tables.pop()
        where = wheres.pop()
        where_is = where_iss.pop()
                    
        phenotype = Phenotype.objects.get(id=where)
        phenotype_type = phenotype.phenotype_type.phenotype_type
                            
        if phenotype_type != 'Affection Status':
            querystr = querystrs.pop().strip()
        else:
            querystr = ''
                                        
        if len(query_results) > 0:
            query_results = query_db_with_ids(table, where, where_is, querystr, query_results)
            query_summary.append("+ FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr)
        else: 
            message = "Sorry your query didn't return any results, please try another query."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
    return query_results, query_summary

def perform_queries_with_ids(request, tables, wheres, where_iss, querystrs, query_results):
    
    query_summary = []
    
    while len(tables) > 0:
        table = tables.pop()
        where = wheres.pop()
        where_is = where_iss.pop()
                    
        phenotype = Phenotype.objects.get(id=where)
        phenotype_type = phenotype.phenotype_type.phenotype_type
                            
        if phenotype_type != 'Affection Status':
            querystr = querystrs.pop().strip()
        else:
            querystr = ''
                                        
        if len(query_results) > 0:
            query_results = query_db_with_ids(table, where, where_is, querystr, query_results)
            query_summary.append("+ FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr)
        else: 
            message = "Sorry your query didn't return any results, please try another query."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
    return query_results, query_summary
                    
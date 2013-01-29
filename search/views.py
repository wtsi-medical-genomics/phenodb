from django.shortcuts import render
from search.models import IndividualIdentifier, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, StudySamples, Phenotype, Platform, Individual, Study, Sample, Source, QC
from search.tables import PhenotypeTable, PlatformTable, StudyTable, QCTable, SourceTable, CountTable
import csv
from django.http import HttpResponse
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json


def home(request):
    return render(request, 'search/home.html', {})

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

def showPhenotypes(request):
    
    phenotypes = Phenotype.objects.all()
    phenotype_values = []
    
    for phenotype in phenotypes:
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            values_dict_array = AffectionStatusPhenotypeValue.objects.filter(phenotype_id=phenotype.id).order_by('phenotype_value').values('phenotype_value').distinct()            
            values_list = []
            for value_dict in values_dict_array:
                values_list.append(str(value_dict['phenotype_value']))
            values_str = ", ".join(values_list)
            not_null_total = AffectionStatusPhenotypeValue.objects.filter(phenotype_id=phenotype.id, phenotype_value__isnull=False).values('phenotype_value').count()
        elif phenotype.phenotype_type.phenotype_type == 'Qualitative':
            values_dict_array = QualitativePhenotypeValue.objects.filter(phenotype_id=phenotype.id).values('phenotype_value').distinct()
            values_list = []
            for value_dict in values_dict_array:
                values_list.append(str(value_dict['phenotype_value']))
            values_str = ", ".join(values_list)
            not_null_total = QualitativePhenotypeValue.objects.filter(phenotype_id=phenotype.id, phenotype_value__isnull=False).values('phenotype_value').count()
        elif phenotype.phenotype_type.phenotype_type == 'Quantitative':
            values_dict_array = QuantitiatvePhenotypeValue.objects.filter(phenotype_id=phenotype.id).order_by('phenotype_value').values('phenotype_value').distinct()
            values_list = []
            for value_dict in values_dict_array:
                values_list.append(value_dict['phenotype_value'])
            if len(values_list) > 0:
                values_str = "...".join((str(min(values_list)), str(max(values_list))))
            else:
                values_list = "" 
            not_null_total = QuantitiatvePhenotypeValue.objects.filter(phenotype_id=phenotype.id, phenotype_value__isnull=False).values('phenotype_value').count()
        
        phenotype_values.append({'name':phenotype.phenotype_name, 'description':phenotype.phenotype_description, 'currently_held_values':values_str, 'not_null_total': not_null_total})
    
    table = PhenotypeTable(phenotype_values)
    return render(request, 'search/dataview.html', {'table': table})

def showIndividuals(request):
    message = "The database currently contains <strong>" + str(Individual.objects.all().count()) + "</strong> individuals"
    message += " and <strong>" + str(IndividualIdentifier.objects.all().count()) + "</strong> individual IDs"
    message += "<br/>Individual IDs by source:"
    sources = Source.objects.all()
    source_counts = []
    for source in sources:
        source_counts.append({'name':source.source_name,'count':IndividualIdentifier.objects.filter(source_id=source.id).count()})
    table = CountTable(source_counts)
    return render(request, 'search/summary.html', {'message': message, 'table': table})

def showSamples(request):
    message = "The database currently contains <strong>" + str(Sample.objects.all().count()) + "</strong> samples"
    message += "<br/>Samples by study:"
    studies = Study.objects.all()
    study_counts = []
    for study in studies:
        study_counts.append({'name':study.study_name,'count':StudySamples.objects.filter(study_id=study.id).count()})
    table = CountTable(study_counts)
    return render(request, 'search/summary.html', {'message': message, 'table': table})

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
        menuitems = [{"value": "true", "text": "True" },{"value": "false", "text": "False"},{"value": "isnull", "text": "Is NULL"},{"value": "notnull", "text": "Is not NULL"}]
    elif phenotype.phenotype_type.phenotype_type == 'Qualitative':        
        menuitems = [{"value": "eq", "text": "Equals" },{"value": "contains", "text": "Contains" },{"value": "starts_with", "text": "Starts with" },{"value": "ends_with", "text": "Ends with" },{"value": "isnull", "text": "Is NULL"},{"value": "notnull", "text": "Is not NULL"}]        
    elif phenotype.phenotype_type.phenotype_type == 'Quantitative':        
        menuitems = [{"value": "eq", "text": "==" },{"value": "gt", "text": ">" },{"value": "gte", "text": ">=" },{"value": "lt", "text": "<" },{"value": "lte", "text": "<=" },{"value": "isnull", "text": "Is NULL"},{"value": "notnull", "text": "Is not NULL"}]        
    return HttpResponse(json.dumps(menuitems), mimetype="application/javascript")

def generate_html_table(output, query_results):
    table_html = "<table class=\"table table-striped table-bordered\">\n"
    for column in output:
        
        ## if the column is a phenotype then get the phenotype name from the id
        if str(column).startswith("phenotype"):               
            phenotype_id = column.split(":")[1] 
            phenotype = Phenotype.objects.get(id=phenotype_id)            
            table_html = "".join((table_html, "<th>"+ phenotype.phenotype_name +"</th>\n"))
        else:
            table_html = "".join((table_html, "<th>"+ column +"</th>\n"))
    for results_row in query_results:
        table_html = "".join((table_html, "<tr>\n"))
        for value in results_row:
            table_html = "".join((table_html, "<td>" + value + "</td>\n"))
        table_html = "".join((table_html, "</tr>\n"))

    return "".join((table_html, "</table>\n"))

def querybuilder(request):
    if request.method == 'POST':        
        results_per_page = 25     # default value
        tables    = request.POST.getlist('from')
        wheres    = request.POST.getlist('where')
        where_iss = request.POST.getlist('is')
        querystrs = request.POST.getlist('querystr')        
        andors    = request.POST.getlist('andor')
        search_in = request.POST['searchIn']        
        output    = request.POST.getlist('output')
        page      = request.GET.get('page')
                
        ## check that all the queries contain something for each required field 
        if len(where_iss) == 0 | all(where_iss) is False | len(wheres) == 0 | all(wheres) is False | len(tables) == 0 | all(tables) is False:
            message = "Query form contains missing information, please complete all fields and try again."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
        ## check that each of the required input fields contains data
        elif len(output) == 0:
            message = "No output columns selected, please select output columns and try again."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
        else:
            ## create strings of the query arrays so that they can be passed between pages
            tables_string    = "_".join(tables)
            wheres_string    = "_".join(wheres)
            where_iss_string = "_".join(where_iss)
            querystr_string  = "_".join(querystrs)
            output_string    = "_".join(output)
            
            ## search all records or from a list of individuals
            if (search_in == 'userlist'):
                user_ids = []                
                if (request.POST['individual_list']):
                    textarea_values = request.POST['individual_list'].splitlines()
                    for line in textarea_values:
                        if (line.strip()):
                            user_ids.append(line.strip())
                                                
                elif (request.FILES['individual_file']):
                    indFile = request.FILES['individual_file']                    
                    if not indFile.multiple_chunks():
                        file_lines = indFile.read().splitlines()                        
                        for line in file_lines:
                            if (line.strip()):
                                user_ids.append(line.strip())                         
                    else:
                        message = "Sorry your file '" + indFile.name + "' is too large to read into memory."
                        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})                    
                                
                if (len(user_ids) > 0):                    
                    # array of tuples
                    db_ids = []                
                    for user_id in user_ids:                                                
                        query_result = IndividualIdentifier.objects.filter(individual_string=user_id).values_list('individual_id')                        
                        if (len(query_result) > 0):
                            # append just the first tuple of the list !?!?
                            db_ids.append(query_result[0])
                                                        
                    if (len(db_ids) > 0):
                        results = perform_queries_with_ids(request, tables, wheres, where_iss, querystrs, db_ids)
                        result_ids = results[0]
                        query_summary = results[1]
                        if len(result_ids) > 0:
                            table = generate_results_table(result_ids, results_per_page, page, output)
                            return render(request, 'search/queryresults.html', {'tablehtml': table[0], 'page_results':table[1], 'output_str': output_string, 'count':len(result_ids), 'tables_str':tables_string, 'where_str':wheres_string, 'whereis_str':where_iss_string, 'querystr_str':querystr_string, 'query_summary':query_summary, 'results_per_page':results_per_page})
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
                                
            elif (search_in ==  'all'):
                query_results = perform_queries(request, tables, wheres, where_iss, querystrs)
                result_ids = query_results[0]
                query_summary = query_results[1] 
                if len(result_ids) > 0:
                    table = generate_results_table(result_ids, results_per_page, page, output)
                    return render(request, 'search/queryresults.html', {'tablehtml': table[0], 'page_results':table[1], 'output_str': output_string, 'count':len(result_ids), 'tables_str':tables_string, 'where_str':wheres_string, 'whereis_str':where_iss_string, 'querystr_str':querystr_string, 'query_summary':query_summary, 'results_per_page':results_per_page})
                else:
                    message = "Sorry your query didn't return any results, please try another query."
                    return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
    else:
        # pass all the phenotypes/platforms/studies etc to the form                 
        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all()})
        
def querypage(request, page, results_per_page, tables_string, wheres_string, where_iss_string, querystr_string, output_string):
    tables = tables_string.split("_")
    wheres = wheres_string.split("_")
    where_iss = where_iss_string.split("_")
    querystrs = querystr_string.split("_")
    output = output_string.split("_")
    
    query_results = perform_queries(request, tables, wheres, where_iss, querystrs)
    result_ids = query_results[0]
    query_summary = query_results[1]

    table = generate_results_table(result_ids, results_per_page, page, output)
    return render(request, 'search/queryresults.html', {'tablehtml': table[0], 'page_results':table[1], 'output_str': output_string, 'count':len(result_ids), 'tables_str':tables_string, 'where_str':wheres_string, 'whereis_str':where_iss_string, 'querystr_str':querystr_string, 'query_summary':query_summary, 'results_per_page':results_per_page})
    
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

def query_db(table, where, where_is, querystr, last_query):
    
    if table == 'phenotype':
        phenotype = Phenotype.objects.get(id=where)            
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            if where_is == 'true':
                result_set =  AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=1).values_list('individual_id')
            elif where_is == 'false':
                result_set =  AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__exact=0).values_list('individual_id')
            elif where_is == 'notnull':
                result_set = AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=False).values_list('individual_id')
            elif where_is == 'isnull':
                result_set = AffectionStatusPhenotypeValue.objects.filter(phenotype__exact=phenotype.id, phenotype_value__isnull=True).values_list('individual_id')
                        
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
        
        if last_query is not None:
            if result_set.count() > 0:
                intersection_set = set(list(last_query)).intersection(set(list(result_set)))
                return list(intersection_set)
            else:   
                return None
        else:
            return result_set                        

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
    for ind_tuple in page_results:
        ind_id = ind_tuple['identifier']
        row_values = []
        for column in output_columns:
            if column == 'IndividualID':                
                ind_strings = IndividualIdentifier.objects.filter(individual_id = ind_id).values('individual_string')                            
                ## if there are more than 1 id then join the strings
                identifier_string = ""
                for i in ind_strings:                    
                    identifier_string = " ".join((i['individual_string'], identifier_string))
                row_values.append(identifier_string)                
            elif column == 'Source':
                ind_objects = IndividualIdentifier.objects.filter(individual_id = ind_id)
                source_string = ""
                for i in ind_objects:
                    source_string = " ".join((i.source.source_name, source_string))
                row_values.append(source_string)
            elif column == 'Sex':
                indObject = Individual.objects.get(id = ind_id)
                if (indObject.sex == 1):
                    row_values.append("Male")
                elif (indObject.sex == 2):
                    row_values.append("Female")
                else:
                    row_values.append("Unkown")
            elif column == 'SampleIDs':
                sample_ids = Sample.objects.filter(individual_id = ind_id).values('sample_id')
                sample_string = ""
                for s in sample_ids:
                    sample_string = " ".join((s['sample_id'], sample_string))    
                row_values.append(sample_string)                
            elif column == 'Study':
                samples = Sample.objects.filter(individual_id = ind_id)
                study_string = ""
                for s in samples:
                    study_string = " ".join((s.studysample.study.study_name, study_string))    
                row_values.append(study_string)
            elif column == 'Platform':
                samples = Sample.objects.filter(individual_id = ind_id)
                platform_string = ""
                for s in samples:
                    platform_string = " ".join((s.studysample.study.platform.platform_name, platform_string))    
                row_values.append(study_string)
#            elif column == 'QC': 
            elif str(column).startswith("phenotype"):               
                phenotype_id = column.split(":")[1] 
                phenotype = Phenotype.objects.get(id=phenotype_id)            
                
                if phenotype.phenotype_type.phenotype_type == 'Affection Status':                    
                    try:
                        affectionstatus = AffectionStatusPhenotypeValue.objects.get(phenotype__exact=phenotype.id, individual_id=ind_id)
                        value = str(affectionstatus.phenotype_value)
                    except AffectionStatusPhenotypeValue.DoesNotExist:
                        value = "-"                                
                elif phenotype.phenotype_type.phenotype_type == 'Qualitative':            
                    try:
                        qualitative = QualitativePhenotypeValue.objects.get(phenotype__exact=phenotype.id, individual_id=ind_id)
                        value = str(qualitative.phenotype_value)
                    except QualitativePhenotypeValue.DoesNotExist:
                        value = "-"            
                elif phenotype.phenotype_type.phenotype_type == 'Quantitative':
                    try:
                        quantitiatve = QuantitiatvePhenotypeValue.objects.get(phenotype__exact=phenotype.id, individual_id=ind_id)
                        value = str(quantitiatve.phenotype_value)
                    except QuantitiatvePhenotypeValue.DoesNotExist:
                        value = "-"            
                
                row_values.append(value)
        
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
                    
    query_results = query_db(table, where, where_is, querystr, None)
                
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
            query_results = query_db(table, where, where_is, querystr, query_results)
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
            query_results = query_db(table, where, where_is, querystr, query_results)
            query_summary.append("+ FROM " + table + " WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr)
        else: 
            message = "Sorry your query didn't return any results, please try another query."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
    return query_results, query_summary

def get_page_results(paginator, page):
    
    try:
        page_results = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_results = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_results = paginator.page(paginator.num_pages)
    
    return page_results

def generate_results_table(result_ids, results_per_page, page, output):
    
    query_ids_objs = parse_query_results(result_ids)
    
    page_results = get_page_results(Paginator(query_ids_objs, results_per_page), page)
    
    table_html = generate_html_table(output, get_output_data(page_results, output))
    
    return table_html, page_results
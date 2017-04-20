# external imports
from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
import json
import io
import time
from collections import defaultdict, OrderedDict
import pprint

## Fudge required for generating plots in production because writing to sys.stdout is by default restricted in versions of mod_wsgi
## This restriction can be disabled by mapping sys.stdout to sys.stderr at global scope within in the WSGI application script file.
import sys
sys.stdout = sys.stderr

# internal imports
from .models import IndividualIdentifier, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Phenotype, Platform, Individual, Study, Sample, Source, QC, Collection, StudySample, PhenodbIdentifier, MissingSampleID
from .tables import PhenotypeTable, PlatformTable, StudyTable, QCTable, SourceTable, CollectionTable, MissingTable, MissingStudyTable, ConflictingSampleIDsTable

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

def showCollections(request):
    table = CollectionTable(Collection.objects.all())
    return render(request, 'search/dataview.html', {'table': table})

def showMissing(request):
    study_counts = []
    for study in Study.objects.all():
        study_counts.append({'study_id': study.id, 'study_name': study.study_name, 'missing_sample_count': MissingSampleID.objects.filter(study_id=study.id).count()})

    table = MissingTable(study_counts)
    return render(request, 'search/dataview.html', {'table': table})

def showMissingStudy(request, study_id):    
    table = MissingStudyTable(MissingSampleID.objects.filter(study_id=study_id))
    return render(request, 'search/dataview.html', {'table': table})

def showPhenotypes(request):
    phenotypes = Phenotype.objects.all()
    phenotype_values = []
    for phenotype in phenotypes:
        values_str = ""
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
        phenotype_values.append({'phenotype_id':phenotype.id, 'phenotype_name':phenotype.phenotype_name, 'description':phenotype.phenotype_description, 'values':values_str, 'total_records': not_null_total})    
    table = PhenotypeTable(phenotype_values)

    return render(request, 'search/dataview.html', {'table': table})

def showIndividuals(request):
    message = "The database currently contains <strong>" + str(Individual.objects.all().count()) + "</strong> individuals"
    message += " and <strong>" + str(IndividualIdentifier.objects.all().count()) + "</strong> individual IDs"
    message += "<br/>Individual IDs by source:"
    
    return render(request, 'search/summary.html', {'message': message})

def getIndividualData(request):
    source_counts = []
    for source in Source.objects.all():
        source_counts.append({'value': source.source_name, 'count': IndividualIdentifier.objects.filter(source_id=source.id).values('individual_id').distinct().count()})
            
    fieldnames = ['value','count']
    headers = dict( (n,n) for n in fieldnames )
    
    myFakeFile = io.StringIO()
    myWriter = csv.DictWriter( myFakeFile, fieldnames, delimiter='\t')
    myWriter.writerow(headers)
    for s in source_counts:
        myWriter.writerow(s)
    
    return HttpResponse(myFakeFile.getvalue(), content_type='text/tab-separated-values')

def showSamples(request):
    message = "The database currently contains <strong>" + str(Sample.objects.all().count()) + "</strong> samples"
    message += "<br/>Samples by study:"
    
    return render(request, 'search/summary.html', {'message': message})

def getSampleData(request):
    study_counts = []
    for study in Study.objects.all():
        study_counts.append({'value': study.study_name, 'count': StudySample.objects.filter(study_id=study.id).count()})
            
    fieldnames = ['value','count']
    headers = dict( (n,n) for n in fieldnames )
    
    myFakeFile = io.StringIO()
    myWriter = csv.DictWriter( myFakeFile, fieldnames, delimiter='\t')
    myWriter.writerow(headers)
    for s in study_counts:
        myWriter.writerow(s)
        
    return HttpResponse(myFakeFile.getvalue(), content_type='text/tab-separated-values')

def showPhenotypePlot(request, phenotype_id):
    phenotype = Phenotype.objects.get(id=phenotype_id)
    return render(request, 'search/barplot.html', {'id': phenotype_id, 'title': phenotype.phenotype_name})

def getPhenotypePlotData(request, phenotype_id):
    phenotype_value_counts = []
    phenotype = Phenotype.objects.get(id=phenotype_id)
    
    if phenotype.phenotype_type.phenotype_type == 'Affection Status':
        values_dict_array = AffectionStatusPhenotypeValue.objects.filter(phenotype_id=phenotype.id).order_by('phenotype_value').values('phenotype_value').distinct()                    
        for value_dict in values_dict_array:
            phenotype_value = str(value_dict['phenotype_value'])
            phenotype_value_count = AffectionStatusPhenotypeValue.objects.filter(phenotype_id=phenotype.id, phenotype_value=phenotype_value).count()
            phenotype_value_counts.append({'value': phenotype_value, 'count': phenotype_value_count})

    elif phenotype.phenotype_type.phenotype_type == 'Qualitative':
        values_dict_array = QualitativePhenotypeValue.objects.filter(phenotype_id=phenotype.id).values('phenotype_value').distinct()
        for value_dict in values_dict_array:
            phenotype_value = str(value_dict['phenotype_value'])
            phenotype_value_count = QualitativePhenotypeValue.objects.filter(phenotype_id=phenotype.id, phenotype_value=phenotype_value).count()
            phenotype_value_counts.append({'value': phenotype_value, 'count': phenotype_value_count})
            
    elif phenotype.phenotype_type.phenotype_type == 'Quantitative':
        values_dict_array = QuantitiatvePhenotypeValue.objects.filter(phenotype_id=phenotype.id).order_by('phenotype_value').values('phenotype_value').distinct()
        for value_dict in values_dict_array:
            phenotype_value = str(value_dict['phenotype_value'])
            phenotype_value_count = QuantitiatvePhenotypeValue.objects.filter(phenotype_id=phenotype.id, phenotype_value=phenotype_value).count()
            phenotype_value_counts.append({'value': phenotype_value, 'count': phenotype_value_count})
                
    ## create a tsv file to pass to the d3 plotting library
    fieldnames = ['value','count']
    headers = dict( (n,n) for n in fieldnames )
    
    myFakeFile = io.StringIO()
    myWriter = csv.DictWriter( myFakeFile, fieldnames, delimiter='\t')
    myWriter.writerow(headers)
    for r in phenotype_value_counts:
        myWriter.writerow(r)    
    
    print(myFakeFile.getvalue())
    
    return HttpResponse(myFakeFile.getvalue(), content_type='text/tab-separated-values')

def all_json_models(request, menuid):
    
    if menuid == 'phenotype':
        menuitems = Phenotype.objects.all()
    elif menuid == 'platform':
        menuitems = Platform.objects.all()
    elif menuid == 'study':
        menuitems = Study.objects.all()
    elif menuid == 'qc':
        menuitems = QC.objects.all()
    elif menuid == 'source':
        menuitems = Source.objects.all()
        
    json_models = serializers.serialize("json", menuitems)
    return HttpResponse(json_models, content_type="application/javascript")

def all_search_options(request, menuid, menuval):
    menuitems = []    
    if menuid == 'phenotype':
        phenotype = Phenotype.objects.get(id=menuval)
        if phenotype.phenotype_type.phenotype_type == 'Affection Status':
            menuitems = [{"value": "true", "text": "True" },{"value": "false", "text": "False"},{"value": "isnull", "text": "Is NULL"},{"value": "notnull", "text": "Is not NULL"}]
        elif phenotype.phenotype_type.phenotype_type == 'Qualitative':        
            menuitems = [{"value": "eq", "text": "Equals" },{"value": "contains", "text": "Contains" },{"value": "starts_with", "text": "Starts with" },{"value": "ends_with", "text": "Ends with" },{"value": "isnull", "text": "Is NULL"},{"value": "notnull", "text": "Is not NULL"}]        
        elif phenotype.phenotype_type.phenotype_type == 'Quantitative':        
            menuitems = [{"value": "eq", "text": "==" },{"value": "gt", "text": ">" },{"value": "gte", "text": ">=" },{"value": "lt", "text": "<" },{"value": "lte", "text": "<=" },{"value": "isnull", "text": "Is NULL"},{"value": "notnull", "text": "Is not NULL"}]
    else:
        menuitems = [{"value": "true", "text": "True" },{"value": "false", "text": "False"}]
        
    return HttpResponse(json.dumps(menuitems), content_type="application/javascript")

def generate_html_table(output, query_results):
    table_html = "<table class=\"table table-striped table-bordered\">"
    table_html = "".join((table_html, "<tr>"))
    for column in output:    
        ## if the column is a phenotype then get the phenotype name from the id
        if str(column).startswith("phenotype"):               
            phenotype_id = column.split(":")[1] 
            phenotype = Phenotype.objects.get(id=phenotype_id)            
            table_html = "".join((table_html, "<th>"+ phenotype.phenotype_name +"</th>"))
        elif str(column).startswith("study"):
            study_id = column.split(":")[1] 
            study = Study.objects.get(id=study_id)            
            table_html = "".join((table_html, "<th>"+ study.study_name +"</th>"))
        else:
            table_html = "".join((table_html, "<th>"+ column +"</th>"))
    table_html = "".join((table_html, "</tr>"))
    for results_row in query_results:
        table_html = "".join((table_html, "<tr>"))
        for value in results_row:
            table_html = "".join((table_html, "<td>" + value + "</td>"))
        table_html = "".join((table_html, "</tr>"))

    return "".join((table_html, "</table>"))

def querybuilder(request):
    if request.method == 'POST':        
        results_per_page = 25     # default value
        tables    = request.POST.getlist('from')
        wheres    = request.POST.getlist('where')
        where_iss = request.POST.getlist('is')
        querystrs = request.POST.getlist('querystr')                        
        output    = request.POST.getlist('output')
        search_in = request.POST.get('searchIn')
        page      = request.GET.get('page')
        andors    = request.POST.getlist('andor')

        print(request)
        print(results_per_page)
        print(tables)
        print(wheres)
        print(where_iss)
        print(querystrs)
        print(output)
        print(search_in)
        print(page)
        print(andors)
                
        if len(output) == 0:
            message = "No output columns selected, please select output columns and try again."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
        else:
#            set the input options for the session 
            request.session['tables']    = list(tables)            
            request.session['wheres']    = list(wheres)
            request.session['where_iss'] = list(where_iss)
            request.session['querystrs'] = list(querystrs)       
            request.session['search_in'] = list(search_in)       
            request.session['output']    = list(output)
            request.session['search_in'] = search_in
            request.session['andors']    = list(andors)            
            
            ## search all records or from a list of individuals
            if search_in == 'userlist':
                user_ids = []                
                if request.POST.get('individual_list'):
                    textarea_values = request.POST.get('individual_list').splitlines()
                    
                    ## to start with lets assume if the line contains two values they are source_id and source
                    ## if the line contains one value then this is a phenodbid
                    
                    for line in textarea_values:
                        if (line.split()):
                            line_vals = str(line.strip()).split(',')
                            print(line_vals)
                            
                            if len(line_vals) == 1:
                                user_ids.append([line_vals[0]])
                            elif len(line_vals) == 2:
                                ## assume source_id source format to start with
                                user_ids.append([line_vals[0],line_vals[1]])
                            else:
                                message = "Sorry the format of your individual list has not been recognised"
                                return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                                                                                
                elif request.FILES.get('individual_file'):
                    indFile = request.FILES.get('individual_file')                    
                    if not indFile.multiple_chunks():
                        file_lines = indFile.read().splitlines()                        
                        for line in file_lines:
                            if (line.split()):
                                line_vals = str.split(str(line.strip()))
                                if len(line_vals) == 1:
                                    user_ids.append([line_vals[0]])
                                elif len(line_vals) == 2:
                                    ## assume source_id source format to start with
                                    user_ids.append([line_vals[0],line_vals[1]])
                                else:
                                    message = "Sorry the format of your individual list has not been recognised"
                                    return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})                                    
                    else:
                        message = "Sorry your file '" + indFile.name + "' is too large to read into memory."
                        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})                                           
                ## get user input to say if ids are phenodbids, sample or supplier
                if len(user_ids) > 0:                    
                    # array of tuples
                    db_ids = []                
                    for user_id in user_ids:
                        start = time.time()
                        if len(user_id) == 1:
                            try:
                                query_result = Sample.objects.filter(sample_id__iexact=user_id[0])[0]
                                
                            except IndexError:
                                # see if the id is a sample id
                                if PhenodbIdentifier.objects.filter(phenodb_id=user_id[0]).count() > 0:
                                    query_result = PhenodbIdentifier.objects.get(phenodb_id=user_id[0])
                                else:
                                    continue
#                             try:
#                                 query_result = PhenodbIdentifier.objects.get(phenodb_id=user_id[0])
#                             except PhenodbIdentifier.DoesNotExist:
#                                 # see if the id is a sample id
#                                 if Sample.objects.filter(sample_id__iexact=user_id[0]).count() > 0:
#                                     query_result = Sample.objects.filter(sample_id__iexact=user_id[0])[0]
#                                 else:
#                                     continue
                                                            
                        elif len(user_id) == 2:
                            try:
                                query_result = IndividualIdentifier.objects.get(individual_string__iexact=user_id[0], source__source_name__iexact=user_id[1])
                            except IndividualIdentifier.DoesNotExist:
                                continue                         
                            
                        ## the individuals need to be in tuples to match the queryset results 
                        individual_tuple = query_result.individual_id,      
                        db_ids.append(individual_tuple)
                        #print 'id search',time.time() - start
                    
                    if len(db_ids) > 0:
                        
                        query_results = perform_queries_with_ids(request, tables, wheres, where_iss, querystrs, db_ids, andors)
                        if query_results is not None:
                            result_ids = query_results[0]
                            query_summary = query_results[1]
                            request.session['user_ids'] = list(db_ids)
                            if len(result_ids) > 0:
                                table = generate_results_table(result_ids, results_per_page, page, output)
                                return render(request, 'search/queryresults.html', {'tablehtml': table[0], 'page_results':table[1], 'count':len(result_ids), 'query_summary':query_summary, 'results_per_page':results_per_page})
                            else:
                                message = "Sorry your query didn't return any results, please try another query."
                                return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                        else:
                            message = "Query form contains missing information, please complete all required fields and try again."
                            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                    else:
                        message = "Sorry none of the individual IDs you provided could be found, please try again."
                        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                else:
                    message = "No individual IDs were input, please try again."
                    return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                                
            elif search_in ==  'all':
                query_results = perform_queries(request, tables, wheres, where_iss, querystrs, andors)
                if query_results is not None:
                    result_ids = query_results[0]
                    query_summary = query_results[1] 
                    if len(result_ids) > 0:
                        table = generate_results_table(result_ids, results_per_page, page, output)
                        return render(request, 'search/queryresults.html', {'tablehtml': table[0], 'page_results':table[1], 'count':len(result_ids), 'query_summary':query_summary, 'results_per_page':results_per_page})
                    else:
                        message = "Sorry your query didn't return any results, please try another query."
                        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
                else:
                    message = "Query form contains missing information, please complete all required fields and try again."
                    return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
    else:
        # pass all the phenotypes to the form to create the output options                 
        return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(), 'studies':Study.objects.all})
        
def querypage(request, page, results_per_page):
    
    tables = request.session.get('tables')
    wheres = request.session.get('wheres')
    where_iss = request.session.get('where_iss')
    querystrs = request.session.get('querystrs')
    output = request.session.get('output')
    search_in = request.session.get('search_in')
    andors    = request.session.get('andors')
    
    if search_in == 'userlist':
        db_ids = request.session.get('user_ids')
        results = perform_queries_with_ids(request, tables, wheres, where_iss, querystrs, db_ids, andors)
        result_ids = results[0]
        query_summary = results[1]
        
    elif search_in ==  'all':
        query_results = perform_queries(request, tables, wheres, where_iss, querystrs, andors)
        result_ids = query_results[0]
        query_summary = query_results[1]
    
    table = generate_results_table(result_ids, results_per_page, page, output)
    return render(request, 'search/queryresults.html', {'tablehtml': table[0], 'page_results':table[1], 'count':len(result_ids), 'query_summary':query_summary, 'results_per_page':results_per_page})
    
def query_export(request):
    tables = request.session.get('tables')
    wheres = request.session.get('wheres')
    where_iss = request.session.get('where_iss')
    querystrs = request.session.get('search_in')
    output = request.session.get('output')
    search_in = request.session.get('search_in')
    andors    = request.session.get('andors')
    
    if search_in == 'userlist':
        db_ids = request.session.get('user_ids')
        results = perform_queries_with_ids(request, tables, wheres, where_iss, querystrs, db_ids, andors)
        result_ids = results[0]
        
    elif search_in ==  'all':
        query_results = perform_queries(request, tables, wheres, where_iss, querystrs, andors)
        result_ids = query_results[0]
        
    result_ids_objs = parse_query_results(result_ids)
    parsed_results = get_output_data(result_ids_objs, output)
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.tsv"'
    
    writer = csv.writer(response, delimiter="\t")

    for e in parsed_results:
        writer.writerow(e)    
    
    return response

def query_db(table, where, where_is, querystr, last_query, andor):
    
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
    elif table == 'source':
        if where_is == 'true':
            result_set = IndividualIdentifier.objects.filter(source=where).values_list('individual_id')
        else:
            result_set = IndividualIdentifier.objects.exclude(source=where).values_list('individual_id')
        
    elif table == 'study':
        if where_is == 'true':
            result_set = Sample.objects.filter(studysample__study=where).values_list('individual_id')
        else:
            result_set = Sample.objects.exclude(studysample__study=where).values_list('individual_id')
    elif table == 'platform':
        if where_is == 'true':
            result_set = Sample.objects.filter(studysample__study__platform=where).values_list('individual_id')
        else:
            result_set = Sample.objects.exclude(studysample__study__platform=where).values_list('individual_id')

    if last_query is not None:
        if result_set.count() > 0:            
            if andor == "and":
                intersection_set = set(list(last_query)).intersection(set(list(result_set)))
                return list(intersection_set)
            elif andor == "or":
                union_set = set(list(last_query)).union(set(list(result_set)))
                return list(union_set)
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
        start = time.time()
        ind_id = ind_tuple['identifier']
        row_values = []
        for column in output_columns:
            if column == 'IndividualID':                
                ind_strings = IndividualIdentifier.objects.filter(individual_id = ind_id).values('individual_string')                            
                identifier_string = ", ".join(v['individual_string'] for v in ind_strings)
                
                row_values.append(identifier_string)
                
            elif column == 'PhenodbID':          
                row_values.append(PhenodbIdentifier.objects.get(individual_id = ind_id).phenodb_id)
                                                
            elif column == 'Source':
                ind_objects = IndividualIdentifier.objects.filter(individual_id = ind_id)
                source_string = ", ".join(i.source.source_name for i in ind_objects)
                
                row_values.append(source_string)
                
            elif column == 'SampleIDs':
                sample_ids = Sample.objects.filter(individual_id = ind_id).distinct().values('sample_id')
                sample_string = ", ".join(s['sample_id'] for s in sample_ids)
                
                row_values.append(sample_string)
                                
            elif column == 'Studies':
                samples = Sample.objects.filter(individual_id = ind_id)                
                study_string = ""
                for s in samples:
                    study_samples = StudySample.objects.filter(sample_id = s)
                    study_string = ", ".join(ss.study.study_name for ss in study_samples)    
                
                row_values.append(study_string)
                
            elif column == 'Platforms':
                samples = Sample.objects.filter(individual_id = ind_id)
                platform_string = ""
                for s in samples:
                    study_samples = StudySample.objects.filter(sample_id = s)
                    platform_string = ", ".join(ss.study.platform.platform_name for ss in study_samples)
                        
                row_values.append(platform_string)
                
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
            elif str(column).startswith("study:"):
                study_id = column.split(":")[1]
                try:
                    ## check if there is a studysample for this study / sample
                    study_sample = StudySample.objects.get(sample__individual__id = ind_id, study=study_id)
                    study_sample_id = study_sample.sample.sample_id
                except StudySample.DoesNotExist:
                    study_sample_id = ""
                except StudySample.MultipleObjectsReturned:
                    ## what if there is more than one entry for the individual?
                    ## such as where we have two sample names that both belong to a study?
                    ## not sure what to do here
                    continue
                    
#                 if StudySample.objects.filter(sample__individual__id = ind_id, study=study_id).count() == 1:
#                     study_sample = StudySample.objects.get(sample__individual__id = ind_id, study=study_id)
#                     study_sample_id = study_sample.sample.sample_id  
#                 for sample in samples: 
#                     if StudySample.objects.filter(sample=sample, study=study).count() == 1:
#                         study_sample_id = sample.sample_id

                row_values.append(study_sample_id)
                           
        parsed_results.append(row_values)
        #print 'results',time.time() - start
    return parsed_results
    
def perform_queries(request, tables, wheres, where_iss, querystrs, andors):
    ## perform the first query: 
    table = tables.pop()
    if table == 'message':
        return None
    where = wheres.pop()
    if where == 'message':
        return None
    andor = andors.pop()
    
    if table == 'source' or table == 'study' or table == 'platform':
        querystr = ''
        where_is = where_iss.pop()
        
        if table == 'source':
            query_summary = ["FROM source " + Source.objects.get(id=where).source_name  + " " + where_is]
        elif table == 'study':
            query_summary = ["FROM study " + Study.objects.get(id=where).study_name  + " " + where_is]
        elif table == 'platform':
            query_summary = ["FROM platform " + Platform.objects.get(id=where).platform_name  + " " + where_is]
        
    elif table == 'phenotype':
        where_is = where_iss.pop()
        if where_is == 'message':
            return None 
        phenotype = Phenotype.objects.get(id=where)
        phenotype_type = phenotype.phenotype_type.phenotype_type
                                            
        if phenotype_type == 'Affection Status' or where_is == 'isnull' or where_is == 'notnull':
            querystr = ''
        else:
            querystr = querystrs.pop().strip()
        
        query_summary = ["FROM phenotype WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr]
                    
    query_results = query_db(table, where, where_is, querystr, None, andor)
    
    ## if there are more queries then perform them on the ids returned from the first query
    while len(tables) > 0:
        table = tables.pop()
        where = wheres.pop()
        andor = andors.pop()
        if table == 'source' or table == 'study' or table == 'platform':            
            querystr = ''
            where_is = where_iss.pop()
        
            if table == 'source':
                query_string = "FROM source " + Source.objects.get(id=where).source_name   + " " + where_is
            elif table == 'study':
                query_string = "FROM study " + Study.objects.get(id=where).study_name  + " " + where_is
            elif table == 'platform':
                query_string = "FROM platform " + Platform.objects.get(id=where).platform_name  + " " + where_is
        
        elif table == 'phenotype':
            where_is = where_iss.pop()                                
            phenotype = Phenotype.objects.get(id=where)
            phenotype_type = phenotype.phenotype_type.phenotype_type
                                            
            if phenotype_type == 'Affection Status' or where_is == 'isnull' or where_is == 'notnull':
                querystr = ''
            else:
                querystr = querystrs.pop().strip()
        
            query_string = "FROM phenotype WHERE " + Phenotype.objects.get(id=where).phenotype_name + " " + where_is + " " + querystr
                                                
        if len(query_results) > 0:
            query_results = query_db(table, where, where_is, querystr, query_results, andor)
            query_summary.append(query_string)
        else: 
            message = "Sorry your query didn't return any results, please try another query."
            return render(request, 'search/querybuilder.html', {'phenotypes':Phenotype.objects.all(),'message':message})
    return query_results, query_summary

def perform_queries_with_ids(request, tables, wheres, where_iss, querystrs, user_ids, andors):
    
    if tables[-1] == 'message':
        return user_ids, ""
    else:
        ## perform all the filtering and then filter out only those in the user id list
        query_results = perform_queries(request, tables, wheres, where_iss, querystrs, andors)  
        result_ids = query_results[0]
        query_summary = query_results[1]
        query_results = set(list(result_ids)).intersection(set(list(user_ids)))
    
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

# TEMP = ['IBD_N5965537', 'gaibdc6035127', 'gaibdc6035274', 'gaibdc6035008', 'gaibdc6034980', 'gaibdc6035041', 'IBD_R5792169', 'IBD_R5792995', 'WTCCC174391', 'gaibdc6034960', 'IBD_N5965271', 'IBD_UC5204817', 'WTCCC174415', 'gaibdc6035324', 'IBD_N5965308', 'gaibdc6035281', 'gaibdc6035271', 'IBD_N5965268', 'IBD_R5799094', 'IBD_N5965547', 'IBD_N5965233', 'gaibdc6035773', 'IBD_N5965763', 'gaibdc6034992', 'CroRep855327', 'IBD_N5965219', 'IBD_R5793074', 'IBD_N5965221', 'CCC2_UC677197', 'IBD_N5965690', 'gaibdc6035221', 'gaibdc6035942', 'IBD_N5965532', 'CroRep855591', 'IBD_N5965376', 'gaibdc6035380', 'WTCCC132989', 'IBD_N5965546', 'gaibdc6036100', 'IBD_EX5372455', 'IBD_R5794289', 'IBD_N5965309', 'gaibdc6035199', 'CroRep833048', 'IBD_N5965249', 'gaibdc6035323', 'WTCCC125552', 'IBD_R5792391', 'SC_WGSC5374561', 'SC_WGSC5374554', 'gaibdc6035235', 'IBD_R5798412', 'WTCCCT505054', 'IBD_N5965465', 'WTCCCT504455', 'IBD_N5965683', 'CroRep855166', 'gaibdc6035213', 'IBD_N5965262', 'IBD_R5792144', 'IBD_UC5417102', 'gaibdc6035052', 'SC_OXFORDIBD5554223', 'gaibdc6036105', 'gaibdc6035194', 'WTCCC73646', 'IBD_UC5417094', 'IBD_N5965252', 'gaibdc6035073', 'SC_OXFORDIBD5554330', 'IBD_N5788853', 'IBD_UC5417389', 'IBD_N5965254', 'IBD_N5965366', 'gaibdc6035490', 'IBD_R5798783', 'WTCCC72009', 'WTCCC72874', 'gaibdc6035205', 'gaibdc6036079', 'gaibdc6035156', 'IBD_CD5406197', 'IBD_CD5145250', 'CroRep855435', 'gaibdc6035385', 'gaibdc6035722', 'gaibdc6035296', 'IBD_N5965564', 'IBD_N5789655', 'CroRep855338', 'IBD_N5788268', 'SC_OXFORDIBD5623877', 'gaibdc6035294', 'IBD_CD5218250', 'gaibdc6035500', 'WTCCC71825', 'gaibdc6035136', 'WTCCC73727', 'gaibdc6034998', 'IBD_UC5417088', 'IBD_N5965286', 'gaibdc6035358', 'SC_WGSC5374589', 'WTCCC72731', 'gaibdc6035077', 'IBD_N5965615', 'gaibdc6036031', 'IBD_R5791732', 'IBD_N5965264', 'gaibdc6035410', 'IBD_Ex5963385', 'gaibdc6035222', 'IBD_N5965278', 'IBD_R5791743', 'IBD_N5965156', 'IBD_R5792423', 'gaibdc6035171', 'IBD_N5965568', 'WTCCC72146', '1794STDY5084350', 'IBD_R5819914', 'IBD_R5798249', 'IBD_N5965187', 'gaibdc6035329', 'WTCCC73839', 'gaibdc6034946', 'IBD_R5798828', 'IBD_CD5144901', 'IBD_Ex5963255', 'IBD_R5798786', 'gaibdc6035095', 'IBD_CD5405677', 'WTCCC132948', 'SC_WGSC5374548', 'gaibdc6034969', 'IBD_R5798788', 'IBD_R5792672', 'IBD_N5965190', 'IBD_N5965155', 'gaibdc6035051', 'WTCCC72725', 'gaibdc6035626', 'WTCCC174510', 'IBD_CD5218215', 'IBD_N5965258', 'CroRep832798', 'IBD_N5788256', 'gaibdc6034964', 'gaibdc6035494', 'IBD_R5792089', 'gaibdc6035004', 'IBD_N5965107', 'IBD_N5965212', 'CroRep854940', 'gaibdc6035234', 'IBD_N5965799', '1794STDY5084755', 'IBD_N5965731', 'gaibdc6035538', 'IBD_N5965277', 'CroRep855517', 'IBD_N5788630', 'SC_WGSC5374547', 'IBD_R5791494', 'IBD_CD5144684', 'IBD_N5965205', 'IBD_R5796379', 'gaibdc6035403', 'IBD_N5965748', 'IBD_CD5145225', 'UC754425', 'IBD_R5792493', 'gaibdc6035269', 'SC_OXFORDIBD5554194', 'IBD_N5965584', 'IBD_CD5203828', 'IBD_N5788436', 'gaibdc6035146', 'IBD_UC5417384', 'gaibdc6035318', 'CroRep831840', 'IBD_R5792275', 'IBD_R5792782', 'IBD_N5965415', 'gaibdc6035343', 'IBD_CD5406140', 'gaibdc6035079', 'gaibdc6034947', 'IBD_N5965644', 'IBD_CD5144965', 'WTCCC175589', 'IBD_N5965211', 'gaibdc6035200', 'WTCCC175485', 'SC_WGSC5374527', 'WTCCC71946', 'gaibdc6035040', 'IBD_R5796096', 'gaibdc6035035', 'gaibdc6035085', 'IBD_UC5219181', 'IBD_N5787517', 'CroRep831890', 'WTCCCT504839', 'IBD_CD5144904', 'IBD_N5965198', 'WTCCCT504777', 'IBD_UC5417142', 'gaibdc6035250', 'CroRep831859', 'IBD_N5965173', 'IBD_N5965191', 'IBD_N5789610', 'gaibdc6035123', 'IBD_R5791507', 'CCC2_UC676942', 'WTCCC87881', 'gaibdc6035326', 'WTCCC72998', 'IBD_R5791615', 'IBD_EX5372354', 'gaibdc6035208', 'IBD_N5965693', 'IBD_CD5145269', 'SC_OXFORDIBD5554471', 'IBD_UC5417079', 'IBD_R5792816', 'IBD_N5965244', 'SC_WGSC5374506', 'IBD_N5965157', 'IBD_UC5417116', 'IBD_N5965246', 'gaibdc6035139', 'gaibdc6035115', 'IBD_N5788865', 'gaibdc6035145', 'IBD_R5798599', 'gaibdc6035144', 'IBD_R5799080', 'gaibdc6035284', 'gaibdc6035306', 'CroRep832057', 'gaibdc6035056', 'WTCCC175447', 'IBD_N5965256', 'gaibdc6035078', 'WTCCC175687', 'WTCCC71804', 'CCC2_UC676944', 'IBD_N5965512', 'IBD_N5965817', 'IBD_N5788907', 'IBD_R5796090', 'IBD_CD5406184', 'IBD_UC5417422', 'IBD_N5965163', 'IBD_N5965516', 'gaibdc6035092', 'IBD_CD5406062', 'SC_WGSC5374553', 'IBD_CD5145158', 'gaibdc6035072', 'IBD_CD5152424', 'WTCCC73711', 'gaibdc6035458', 'gaibdc6034948', 'IBD_R5791823', 'IBD_N5965281', 'IBD_R5792218', 'CroRep854690', 'WTCCCT505024', 'IBD_N5965225', 'gaibdc6035014', 'IBD_UC5146995', 'gaibdc6035391', 'IBD_N5965287', 'gaibdc6035067', 'IBD_N5965206', 'WTCCC71744', 'PO_IBD1615493', 'WTCCCT504900', 'IBD_R5799114', 'gaibdc6035285', 'IBD_N5788235', 'gaibdc6034965', 'IBD_N5965639', 'UC754674', 'CroRep855560', 'gaibdc6034982', 'gaibdc6035009', 'IBD_N5965394', 'IBD_N5789571', 'CroRep855329', 'IBD_R5796684', 'IBD_UC5146632', 'IBD_N5965201', 'IBD_N5965194', 'gaibdc6035262', 'WTCCC73975', 'gaibdc6035218', 'SC_WGSC5374592', 'IBD_CD5144872', 'gaibdc6035261', 'CroRep855411', 'IBD_N5965091', 'gaibdc6035055', 'IBD_R5796117', 'WTCCC132964', 'IBD_UC5417096', 'WTCCC73319', 'WTCCC73211', 'IBD_CD5144866', 'gaibdc6035207', 'gaibdc6035182', 'gaibdc6035425', 'IBD_N5965526', 'IBD_R5798889', 'IBD_Ex5925023', 'gaibdc6035295', 'WGSC5131985', 'gaibdc6035571', 'IBD_R5796065', 'SC_WGSC5374562', 'gaibdc6034951', 'IBD_N5965207', 'IBD_N5965209', 'CroRep855301', 'WTCCC175219', 'WTCCCT516626', 'IBD_N5789288', 'gaibdc6036123', 'WTCCC73621', 'IBD_R5798867', 'IBD_CD5145166', '1794STDY5084504', 'IBD_N5965248', 'IBD_N5965266', 'IBD_R5792238', 'gaibdc6035214', 'gaibdc6035074', 'gaibdc6035036', 'IBD_Ex5963851', 'IBD_UC5417383', 'IBD_R5791537', 'IBD_N5965259', 'IBD_N5965754', 'CroRep855605', 'gaibdc6035192', 'IBD_N5965241', 'IBD_N5965263', 'CroRep832769', 'IBD_Ex5964481', 'gaibdc6035940', 'WTCCCT504592', 'IBD_CD5144911', 'IBD_R5792683', 'IBD_N5965311', 'IBD_N5965182', '1794STDY5084441', 'WTCCC87803', 'CroRep831660', 'IBD_N5965204', 'IBD_Ex5963231', 'IBD_UC5147026', 'CroRep855608', 'gaibdc6035162', 'IBD_R5792810', 'IBD_N5965239', 'WTCCCT504543', 'WTCCCT516453', 'IBD_N5965275', 'IBD_UC5147354', 'IBD_N5965213', 'IBD_R5792271', 'IBD_R5798683', 'CroRep855306', 'IBD_R5797907', 'IBD_N5965312', 'IBD_CD5145200', 'gaibdc6035015', 'IBD_CD5145165', 'gaibdc6035183', 'IBD_R5798834', 'IBD_R5792985', 'IBD_N5965250', 'IBD_N5965363', 'gaibdc6035061', 'IBD_R5798596', 'IBD_N5965235', 'IBD_R5796012', 'IBD_N5965181', 'IBD_N5965306', 'IBD_CD5218279', 'IBD_N5965298', 'IBD_R5797186', 'IBD_R5798588', 'gaibdc6034955', 'IBD_R5797726', 'IBD_N5965193', 'SC_WGSC5374550', 'IBD_N5787994', 'IBD_CD5406185', 'IBD_N5965195', 'IBD_N5789300', 'IBD_R5796115', 'IBD_CD5144677', 'gaibdc6034991', 'IBD_N5788462', 'IBD_Ex5963751', 'SC_OXFORDIBD5623879', 'IBD_CD5405691', 'gaibdc6035360', 'IBD_R5793988', 'IBD_N5965478', 'IBD_N5965185', 'IBD_R5791699', 'IBD_R5798382', 'IBD_N5965701', 'IBD_N5965580', 'WTCCC71777', 'CroRep832194', 'gaibdc6035307', 'IBD_N5965218', 'gaibdc6035169', 'gaibdc6035219', 'CCC2_UC676934', 'IBD_UC5417090', 'IBD_CD5145221', 'IBD_R5793041', 'IBD_R5793038', 'IBD_CD5203800', 'IBD_CD5406136', 'SC_OXFORDIBD5554728', 'gaibdc6035159', 'gaibdc6036099', 'IBD_N5965560', 'IBD_R5796322', 'IBD_N5965186', 'IBD_N5965220', 'WTCCC175288', 'gaibdc6035058', 'IBD_N5965448', 'WTCCC72784', 'IBD_CD5203820', 'IBD_R5793140', 'IBD_N5965240', 'gaibdc6035026', 'IBD_R5792827', 'IBD_N5965351', 'IBD_R5798324', 'gaibdc6035181', 'IBD_N5965202', 'gaibdc6035927', 'IBD_N5965280', 'IBD_N5965588', 'IBD_N5965226', 'gaibdc6035168', 'IBD_Ex5963766', 'gaibdc6035634', 'WTCCC73597', 'WTCCC71991', 'gaibdc6035319', 'IBD_R5792411', 'gaibdc6035395', 'CroRep831911', 'IBD_N5965659', 'WTCCCT504724', 'CroRep855426', '1794STDY5084487', 'IBD_UC5417080', 'gaibdc6035161', 'gaibdc6035142', 'IBD_N5788834', 'gaibdc6035268', 'gaibdc6035312', 'gaibdc6035254', 'UC754438', 'gaibdc6035117', 'gaibdc6035094', 'WTCCCT505042', 'IBD_R5798871', 'gaibdc6035365', 'IBD_UC5204804', 'IBD_R5798811', 'IBD_N5965171', 'IBD_EX5371858', 'IBD_R5791584', 'IBD_N5965299', 'gaibdc6035678', 'gaibdc6035308', 'IBD_UC5417387', 'UC754602', 'CCC2_UC676943', 'IBD_N5965075', 'gaibdc6035577', 'UC754761', 'gaibdc6035007', 'IBD_N5965243', 'gaibdc6035112', 'IBD_N5965714', 'WTCCC175664', 'gaibdc6035075', 'WTCCC73735', 'IBD_N5965357', 'IBD_CD5145212', 'gaibdc6035301', 'gaibdc6035140', 'gaibdc6035108', 'gaibdc6035091', 'IBD_N5965200', 'IBD_CD5145264', 'IBD_N5965234', 'gaibdc6035193', 'IBD_N5787820', 'WTCCC73566', 'IBD_R5792066', 'IBD_N5965224', 'gaibdc6035267', 'IBD_N5965325', 'IBD_Ex5963742', 'gaibdc6035399', 'gaibdc6034972', 'IBD_R5791832', 'IBD_N5788316', 'IBD_UC5204816', 'UC754630', 'CroRep855360', 'IBD_CD5145539', 'gaibdc6035163', 'gaibdc6034973', 'IBD_N5965164', 'SC_WGSC5374526', 'gaibdc6035293', 'gaibdc6034952', 'IBD_N5965174', 'WTCCCT505029', 'gaibdc6035974', 'IBD_CD5145000', 'IBD_CD5144910', 'gaibdc6035225', 'gaibdc6035098', 'IBD_N5965291', 'IBD_N5965304', 'WTCCC72679', 'IBD_N5965364', 'IBD_N5965743', 'IBD_CD5406137', 'IBD_N5965738', 'IBD_R5792788', 'CroRep855416', 'gaibdc6035443', 'IBD_N5965274', 'gaibdc6034954', 'gaibdc6035257', 'WTCCC175216', 'IBD_R5791530', 'IBD_N5965657', 'CroRep855324', 'IBD_R5819915', 'IBD_N5965273', 'IBD_N5965183', 'IBD_N5965327']
# TEMP = ['WTCCC113721', 'WTCCCT515802', 'WTCCC73964', 'IBD_CD5145569', 'gaibdc6035021', 'IBD_20135522123', 'IBD_CD5203277', 'IBD_N5788244', 'UC180181', 'WTCCC113649', 'IBD_N5965350', 'IBD_N5787933', 'IBD_UC5152993', 'IBD_N5965061', 'SC_OXFORDIBD5554412', 'IBD_N5786949', 'WTCCC87795', 'IBD_20135522173', 'UC179971', 'gaibdc6035834', 'WTCCC71811', 'SC_OXFORDIBD5554350', 'WTCCC132981', 'WTCCC73740', 'WTCCC87832', 'IBD_N5789498', 'IBD_Ex5925033', 'IBD_R5793599', 'SC_OXFORDIBD5554340', 'IBD_Ex5963549', 'IBD_UC5147764', 'IBD_R5791570', 'IBD_N5788253', 'IBD_Ex5963580', 'IBD_N5787242', 'IBD_CD5145747', 'IBD_N5965101', 'WTCCC132988', 'IBD_N5787010', 'IBD_Ex5964485', 'CroRep832084', 'SC_OXFORDIBD5554458', 'WTCCC87847', 'SC_OXFORDIBD5554637', 'UC179998', '1794STDY5084759', 'gaibdc6035539', 'IBD_R5791641', 'IBD_R5793227', 'IBD_EX5371875', 'UC179913', 'UC186378', 'SC_OXFORDIBD5554291', 'WTCCCT516368', 'IBD_N5788262', 'gaibdc6035176', 'WTCCC189307', 'IBD_N5965452', 'UC180086', 'IBD_N5788241', 'IBD_N5788272', 'IBD_CD5145748', 'SC_OXFORDIBD5623985', 'UC180045', 'gaibdc6035546', 'IBD_R5796304', 'SC_WGSC5374658', 'IBD_N5786970', 'IBD_N5965100', 'IBD_N5788466', 'gaibdc6035920', 'IBD_EX5372381', 'IBD_N5788257', 'SC_OXFORDIBD5554675', 'IBD_N5788252', 'gaibdc6035474', 'PO_IBD1615543', 'IBD_N5787040', 'gaibdc6035504', 'CroRep831941', 'WTCCC113773', 'UC179884', 'SC_OXFORDIBD5554649', 'UC180272', 'SC_OXFORDIBD5554443', 'gaibdc6035556', 'IBD_Ex5963534', 'gaibdc6035975', 'UC180039', 'IBD_EX5372247', 'WTCCC174406', 'IBD_N5788233', 'IBD_N5788065', 'IBD_N5788229', 'IBD_N5787771', 'gaibdc6035567', 'WTCCC174387', 'SC_OXFORDIBD5554673', 'WTCCCT516308', 'SC_OXFORDIBD5554525', 'SC_OXFORDIBD5554371', 'IBD_N5787776', 'gaibdc6035738', 'IBD_N5788282', 'IBD_N5788261', 'IBD_N5787690', 'SC_OXFORDIBD5554084', 'SC_OXFORDIBD5554238', 'WTCCC113739', 'IBD_EX5372347', 'SC_OXFORDIBD5554410', 'SC_OXFORDIBD5554548', 'IBD_EX5372001', 'IBD_N5789466', 'UC180136', 'IBD_EX5372287', 'IBD_N5965505', 'WTCCC87848', 'WTCCC72115', 'IBD_N5787592', 'IBD_R5791826', 'gaibdc6035586', '1794STDY5084033', '1794STDY5084753', 'SC_OXFORDIBD5554161', 'gaibdc6035579', 'gaibdc6035290', 'SC_OXFORDIBD5554197', 'IBD_N5789640', 'CroRep831946', 'IBD_N5788862', '1794STDY5084535', 'gaibdc6035597', 'IBD_N5789552', 'IBD_N5787679', 'IBD_N5788417', 'IBD_N5789032', 'SC_OXFORDIBD5554725', 'gaibdc6035594', 'UC179929', 'SC_OXFORDIBD5554678', 'IBD_20135522153', 'IBD_N5965737', 'gaibdc6035922', 'WTCCC175693', 'IBD_R5793600', 'IBD_Ex5963620', 'SC_OXFORDIBD5554647', 'gaibdc6035516', 'UC180266', 'gaibdc6035442', 'CroRep831992', 'IBD_Ex5963660', 'IBD_CD5203852', 'IBD_Ex5963248', 'IBD_CD5203822', 'SC_OXFORDIBD5554588', 'IBD_N5788942', '1794STDY5084738', 'IBD_UC5204770', 'WTCCCT516193', 'IBD_CD5145757', 'IBD_N5965180', 'gaibdc6035492', 'SC_OXFORDIBD5554328', 'IBD_EX5390198', 'IBD_CD5405859', 'gaibdc6035491', 'WTCCC73841', 'IBD_EX5372161', 'IBD_N5787842', 'IBD_N5788027', 'UC180089', 'CroRep729122', 'SC_OXFORDIBD5623953', 'IBD_N5787763', 'WTCCC87838', 'IBD_N5788248', 'WTCCC174575', 'IBD_N5789143', 'IBD_20135522104', 'gaibdc6035604', 'SC_OXFORDIBD5554556', 'CroRep831988', 'IBD_CD5145207', 'gaibdc6035482', 'IBD_N5965383', 'gaibdc6035967', 'IBD_N5789317', 'IBD_CD5145785', 'WTCCC72155', 'IBD_N5787742', 'WTCCC87788', 'SC_OXFORDIBD5623897', 'IBD_N5788303', 'IBD_Ex5963744', 'IBD_EX5390201', 'gaibdc6035507', 'CroRep832707', 'IBD_N5788088', 'IBD_CD5145403', 'IBD_N5786940', 'WTCCC174521', 'IBD_N5965076', 'gaibdc6035122', 'IBD_Ex5963381', 'UC179932', 'SC_OXFORDIBD5554182', 'WTCCC72912', 'IBD_N5965305', 'IBD_R5793498', 'UC179907', 'IBD_N5788427', 'IBD_N5789608', 'IBD_N5965109', 'SC_OXFORDIBD5554583', 'IBD_CD5405661', 'UCW2R11559542', 'IBD_N5788271', 'IBD_20135522112', 'IBD_UC5417789', 'IBD_N5788277', 'IBD_N5787171', 'WTCCC175705', 'SC_OXFORDIBD5554529', 'IBD_EX5372176', 'WTCCCT516212', 'gaibdc6035550', 'IBD_N5965769', 'IBD_CD5145364', 'SC_OXFORDIBD5554286', 'gaibdc6035584', 'IBD_EX5372207', 'WTCCC175680', 'IBD_N5787072', 'IBD_N5789395', 'IBD_Ex5964482', 'gaibdc6035505', 'SC_OXFORDIBD5554736', 'IBD_CD5406325', 'SC_OXFORDIBD5554386', 'SC_OXFORDIBD5554308', 'WTCCC72016', '1794STDY5084562', 'IBD_R5796094', 'WTCCC175573', 'SC_OXFORDIBD5554154', 'UC180194', 'IBD_N5965063', 'SC_OXFORDIBD5554222', 'WTCCC175440', 'CroRep854666', 'IBD_CD5145575', 'WTCCC72116', 'WTCCC71819', 'gaibdc6035957', 'IBD_CD5405261', 'gaibdc6035542', 'CroRep831693', 'IBD_N5788430', 'SC_OXFORDIBD5554522', 'gaibdc6035089', 'UC186371', 'IBD_N5787782', 'gaibdc6035485', 'WTCCC72152', 'SC_OXFORDIBD5554695', 'WTCCC73906', 'WTCCC175236', 'WTCCCT516367', 'SC_OXFORDIBD5554272', '1794STDY5084542', 'IBD_N5787175', 'WTCCC125554', 'IBD_R5796216', 'UC749447', 'gaibdc6035394', 'WTCCCT501606', 'IBD_N5789377', 'SC_OXFORDIBD5623988', 'IBD_N5788254', 'WTCCCT501058', 'CroRep831669', 'gaibdc6035467', 'IBD_N5788276', 'WTCCC71957', 'IBD_N5788333', 'SC_OXFORDIBD5623901', 'gaibdc6036094', 'IBD_N5965684', 'IBD_N5789412', 'SC_OXFORDIBD5554497', 'WTCCCT504577', 'IBD_CD5203275', 'SC_OXFORDIBD5554166', 'IBD_N5965154', 'IBD_N5965618', 'IBD_N5788066', 'IBD_N5788118', 'IBD_UC5153125', 'gaibdc6036122', 'SC_OXFORDIBD5554689', 'IBD_N5788008', 'CroRep855179', 'WTCCC175656', 'WTCCC73029', 'SC_OXFORDIBD5554712', 'gaibdc6035964', 'UC180072', 'IBD_Ex5963422', 'gaibdc6035175', 'IBD_N5788032', 'IBD_N5788439', 'SC_OXFORDIBD5554517', 'IBD_N5787749', 'WTCCC113738', 'IBD_N5965232', 'IBD_N5789569', 'IBD_EX5371797', 'IBD_N5788260', 'IBD_N5965790', 'WTCCC73152', 'IBD_N5787063', 'WTCCC87794', '1794STDY5084342', 'IBD_N5788237', 'gaibdc6035523', 'SC_OXFORDIBD5554212', 'SC_OXFORDIBD5554735', 'WTCCC73569', 'gaibdc6035596', 'WTCCC132940', 'IBD_EX5390234', 'SC_OXFORDIBD5554289', 'CroRep832319', 'IBD_N5786798', 'IBD_N5788236', 'WTCCCT504969', 'IBD_N5788757', 'IBD_N5788320', 'IBD_N5965682', 'IBD_N5786944', 'IBD_20135522176', 'IBD_Ex5963778', 'SC_OXFORDIBD5554710', '1794STDY5084344', 'WTCCC73812', 'gaibdc6035918', 'IBD_CD5203306', 'WTCCC71959', 'IBD_Ex5964518', 'WTCCC71760', 'IBD_UC5146621', 'gaibdc6035495', 'IBD_N5965696', 'IBD_N5788266', 'IBD_N5788267', 'IBD_N5787918', 'SC_OXFORDIBD5554613', 'WTCCC73102', 'SC_OXFORDIBD5554686', 'IBD_N5786983', 'SC_OXFORDIBD5554684', 'SC_OXFORDIBD5554320', 'WTCCC174552', 'IBD_N5787753', 'IBD_N5788453', 'WTCCC132945', 'SC_OXFORDIBD5554740', 'WTCCC73709', 'IBD_R5794279', 'IBD_N5788245', 'WTCCC175493', 'IBD_N5787760']


def duplicateSampleIDs(request):
    samples = Sample.objects.all().select_related('individual')
    individualidentifiers = IndividualIdentifier.objects.all().select_related('source')

    duplicates = defaultdict(list)

    samples2individuals = defaultdict(set)
    individuals2samples = defaultdict(set)
    for sample in samples:
        samples2individuals[sample.sample_id].add(sample.individual)
        individuals2samples[sample.individual_id].add(sample.sample_id)

    for sample, individuals in samples2individuals.items():
        if len(individuals) == 1:
            continue
        individualids = set([x.id for x in individuals])
        if len(individualids) == 1:
            continue
        individualids = tuple(sorted(individualids))
        if individualids in duplicates:
            continue
        
        for individual in individuals:
            queryset = IndividualIdentifier.objects.filter(individual=individual)
            result = defaultdict(set)
            for query in queryset:
                result[query.source.source_name].add(query.individual_string)
            ids_sources = {}
            for k,v in result.items():
                ids_sources[k] = ', '.join(sorted(v))
            
            sample_ids = ', '.join(sorted(individuals2samples[individual.id]))
            duplicates[individualids].append({
                'phenodbid': f'pdb{individual.id}',
                'date': individual.date_created,
                'individual_identifier_sources': ids_sources,
                'sample_ids': sample_ids,
            })
    warning = f'{len(duplicates)} samples are attached to different phenodb IDs.'
    return render(request, 'search/duplicateSampleIDs.html', {
        'duplicate_samples': dict(duplicates),
        'warning': warning,
    })


def conflictingSampleIDs(request):
    samples = Sample.objects.all()
    individual_ids = defaultdict(set)
    date_createds = defaultdict(dict)
    for sample in samples:
        individual_ids[sample.sample_id].add(sample.individual_id)
        date_createds[sample.sample_id][sample.individual_id] = sample.date_created.strftime('%Y-%m-%d')
    
    duplicate_samples = defaultdict(list)
    for sample_id, individual_id in individual_ids.items():
        if len(individual_id) > 1:
            for i in individual_id:
                other_sample_ids = samples.filter(individual_id=i).exclude(sample_id=sample_id)
                other_sample_ids = [x.sample_id for x in other_sample_ids]
                other_sample_ids = ', '.join(sorted(other_sample_ids))
                duplicate_samples[sample_id].append({
                    'phenodbid': f'pdb{i}',
                    'date': date_createds[sample_id][i],
                    'individual_identifier_sources': get_individual_identifier_sources(i),
                    'other_sample_ids': other_sample_ids,
                })
    warning = f'{len(duplicate_samples)} samples are attached to different phenodb IDs.'
    # table = ConflictingSampleIDsTable(duplicate_samples)
    return render(request, 'search/conflictingSampleIDs.html', {
        'duplicate_samples': dict(duplicate_samples),
        'warning': warning,
    })

def get_individual_identifier_sources(individual):
    queryset = IndividualIdentifier.objects.filter(individual=individual)
    result = defaultdict(set)
    for query in queryset:
        result[query.source.source_name].add(query.individual_string)
    prettier_result = {}
    for k,v in result.items():
        prettier_result[k] = ', '.join(sorted(v))
    return prettier_result

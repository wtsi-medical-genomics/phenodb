# external imports
from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
import json
import io
import time

## Fudge required for generating plots in production because writing to sys.stdout is by default restricted in versions of mod_wsgi
## This restriction can be disabled by mapping sys.stdout to sys.stderr at global scope within in the WSGI application script file.
import sys
sys.stdout = sys.stderr

# internal imports
from search.models import IndividualIdentifier, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Phenotype, Platform, Individual, Study, Sample, Source, QC, Collection, StudySample, PhenodbIdentifier, MissingSampleID
from search.tables import PhenotypeTable, PlatformTable, StudyTable, QCTable, SourceTable, CollectionTable, MissingTable, MissingStudyTable

def foo(request):
    return HttpResponse('Hi there')

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
    
    myFakeFile = StringIO.StringIO()
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
    
    myFakeFile = StringIO.StringIO()
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
    
    myFakeFile = StringIO.StringIO()
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
    return HttpResponse(json_models, mimetype="application/javascript")

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
        
    return HttpResponse(json.dumps(menuitems), mimetype="application/javascript")

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
        
    response = HttpResponse(mimetype='text/csv')
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
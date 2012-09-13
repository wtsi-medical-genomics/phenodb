from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from search.models import IndividualIdentifier, Phenotype, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample
from django.core.urlresolvers import reverse

from django import forms

import django_tables2 as tables
from django_tables2 import RequestConfig

class SearchForm(forms.Form):
    id_textarea = forms.CharField(widget=forms.Textarea)

class individualTable(tables.Table):
    individual_id = tables.Column()
    sex = tables.Column()
    source = tables.Column()
    
    class Meta:
        attrs = {'class': 'table table-striped table-bordered'}

class phenotypeTable(tables.Table):
    phenotype_name = tables.Column()
    phenotype_type = tables.Column()
    phenotype_description = tables.Column()
    
    class Meta:
        attrs = {'class': 'table table-striped table-bordered'}

    
def home(request):
    return render(request, 'search/home.html', {})

def showPhenotypes(request):
    table = phenotypeTable(Phenotype.objects.all())
    return render_to_response('search/phenotypes.html', {'table': table}, context_instance=RequestContext(request))

def idSearch(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid(): # All validation rules pass
            
            textarea_values = form.cleaned_data['id_textarea'].splitlines()
            
            ## for each id
            inds = []
            for line in textarea_values:
                query_id = line.strip()
                query_results = IndividualIdentifier.objects.filter(individual_string=query_id)                
                if query_results.count() > 0:                                                
                    for ind in query_results:
#                        sample_results = Sample.objects.filter(individual=ind)                    
#                        affection_results = AffectionStatusPhenotypeValue.objects.filter(individual=ind)                     
#                        qualitative_results = QualitativePhenotypeValue.objects.filter(individual=ind)                    
#                        quantitiative_results = QuantitiatvePhenotypeValue.objects.filter(individual=ind)
                        ind_results = {'individual_id':ind.individual_string,
                                       'sex':ind.individual.sex,
                                       'source':ind.source.source_name
                                       }
                        inds.append(ind_results)
            table = individualTable(inds)
            return render_to_response('search/idresults.html', {'table': table}, context_instance=RequestContext(request))
#            else:
#            id not found

    else:
        form = SearchForm() # An unbound form
        return render(request, 'search/idsearch.html', {'form': form,})

def querybuilder(request):
    return HttpResponse("function not yet implimented")
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from search.models import IndividualIdentifier, Phenotype, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample
from django.core.urlresolvers import reverse

from django import forms

class SearchForm(forms.Form):
    id_field = forms.CharField(max_length=100)

def home(request):
    return render(request, 'search/home.html', {})

def showPhenotypes(request):
    query_results = Phenotype.objects.all()
    return render_to_response('search/phenotypes.html', {'query_results': query_results})

def idSearch(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid(): # All validation rules pass
            query_id = form.cleaned_data['id_field'].strip()    
            query_results = IndividualIdentifier.objects.filter(individual_string=query_id)
            
            if query_results.count() > 0:
                
                ind_results = dict()
                
                for ind in query_results:
                    sample_results = Sample.objects.filter(individual=ind)
                    ind_results['sample_results'] = sample_results
                    affection_results = AffectionStatusPhenotypeValue.objects.filter(individual=ind)
                    ind_results['affection_results'] = affection_results 
                    qualitative_results = QualitativePhenotypeValue.objects.filter(individual=ind)
                    ind_results['qualitative_results'] = qualitative_results 
                    quantitiative_results = QuantitiatvePhenotypeValue.objects.filter(individual=ind)
                    ind_results['quantitiative_results'] = quantitiative_results  
                    
                    
                    
                ## for each ind that is found:
                ## get all samples
                ## get all phenotypes
                
                
                
                return render_to_response('search/iddetails.html', {'query_results': ind_results})
#                url = reverse('idresults', kwargs={'indId': indId.individual.id})                
#                return HttpResponseRedirect(url)
#            else:
                ## id not found
    else:
        form = SearchForm() # An unbound form
        return render(request, 'search/idsearch.html', {'form': form,})

def idResults(request):
    return HttpResponse("function not yet implimented")


def querybuilder(request):
    return HttpResponse("function not yet implimented")
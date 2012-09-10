from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from search.models import IndividualIdentifier, Phenotype
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
                ## if there is more than one match the  print each one for the user to select the correct one                
                if query_results.count() > 1:
                    url = reverse('idselect', kwargs={'query_results': query_results})
                    return HttpResponseRedirect(url)
                else:
                    indId = IndividualIdentifier.objects.get(individual_string=query_id)
                    url = reverse('idresults', kwargs={'indId': indId.individual.id})
                    return HttpResponseRedirect(url)
            else:
                ## id not found
                HttpResponseRedirect('/search/idsearch')
    else:
        form = SearchForm() # An unbound form
        return render(request, 'search/idsearch.html', {'form': form,})

def idResults(request):
    return HttpResponse("function not yet implimented")


def querybuilder(request):
    return HttpResponse("function not yet implimented")
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from search.models import IndividualIdentifier, Phenotype, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample
from django.core.urlresolvers import reverse

from django import forms

class SearchForm(forms.Form):
    id_textarea = forms.widgets.Textarea(attrs={'rows':4, 'cols':60})

def home(request):
    return render(request, 'search/home.html', {})

def showPhenotypes(request):
    query_results = Phenotype.objects.all()
    return render_to_response('search/phenotypes.html', {'query_results': query_results})

def idSearch(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid(): # All validation rules pass
            
            textarea_values = form.cleaned_data['id_textarea'].splitlines()
                        
            ## for each id
            for line in textarea_values:
                query_id = line.strip()
                query_results = IndividualIdentifier.objects.filter(individual_string=query_id)
                
                if query_results.count() > 0:                
                    inds = []                
                    for ind in query_results:
                        sample_results = Sample.objects.filter(individual=ind)                    
                        affection_results = AffectionStatusPhenotypeValue.objects.filter(individual=ind)                     
                        qualitative_results = QualitativePhenotypeValue.objects.filter(individual=ind)                    
                        quantitiative_results = QuantitiatvePhenotypeValue.objects.filter(individual=ind)
                        ind_results = {'ind':ind,'samples':sample_results,'aff':affection_results,'qual':qualitative_results,'quant':quantitiative_results}
                        inds.append(ind_results)
                    return render_to_response('search/idresults.html', {'query_results': inds})
#            else:
#            id not found

    else:
        form = SearchForm() # An unbound form
        return render(request, 'search/idsearch.html', {'form': form,})

def idResults(request):
    return HttpResponse("function not yet implimented")


def querybuilder(request):
    return HttpResponse("function not yet implimented")
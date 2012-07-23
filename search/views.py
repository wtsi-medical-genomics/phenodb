from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from search.models import IndividualIdentifier

from django import forms

class SearchForm(forms.Form):
    id_field = forms.CharField(max_length=100)

def home(request):
    return render(request, 'search/home.html', {})

def idSearch(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid(): # All validation rules pass
            ## get the string and forward to results view
            
            ## find the individual id 
            print IndividualIdentifier.objects.filter(individual_string=form.cleaned_data['id_field'].strip()).count()
            
            
            return  HttpResponseRedirect()
    else:
        form = SearchForm() # An unbound form
        return render(request, 'search/idsearch.html', {'form': form,})

def idResults(request):
    return HttpResponse("function not yet implimented")


def querybuilder(request):
    return HttpResponse("function not yet implimented")
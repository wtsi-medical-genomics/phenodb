from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from django import forms

class SearchForm(forms.Form):
    id_field = forms.CharField(max_length=100)
    id_list = forms.Textarea()
    id_file = forms.FileField()

def home(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            ## search the database for individual id
            ## for each individual return all phenotypes and samples
            
            ## this view needs to generate an output file as well as display results
            
            ## create an id list from either text fields or file
            
            
            ## for each id
                ## get individual
                ##IndividualIdentifier.objects.get(individual_string=id):
                ## get all phenotypes
                ## get all samples
                ## get studies and platforms
                
            
                
            
            
            
            
            
            
            
            return HttpResponseRedirect('/results/')
    else:
        form = SearchForm() # An unbound form

    return render_to_response(request, 'search/home.html', {'form': form,})
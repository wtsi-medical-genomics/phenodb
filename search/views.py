from django.template import Context, loader
from django.http import HttpResponse
from search.admin import BulkUploadForm
from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request):
    t = loader.get_template('search/index.html')
    c = Context({ })
    return HttpResponse(t.render(c))
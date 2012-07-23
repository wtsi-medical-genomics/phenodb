from django.conf.urls import patterns, include, url

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('search.views',
    url(r'^search/$', 'home'),
    url(r'^search/idsearch/$', 'idSearch'),
    url(r'^search/idsearch//$', 'idResults'),
    url(r'^search/querybuilder/$', 'querybuilder'),
#    url(r'^search/results/$', 'results'),
#    url(r'^search/builder/$', 'builder'),
#    url(r'^search/(?P<individualidentifier_id>\d+)/results/$', 'results'),
#    url(r'^search/(?P<individualidentifier_id>\d+)/builder/results/$', 'builderResults'),
    url(r'^admin/', include(admin.site.urls)),
)


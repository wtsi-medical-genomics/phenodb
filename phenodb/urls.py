from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('search.views',
    url(r'^search/$', 'home'),
    url(r'^search/querybuilder/$', 'querybuilder'),
    url(r'^search/querybuilder/(?P<menuid>[-\w]+)/all_json_models/$', 'all_json_models'),
    url(r'^search/querybuilder/(?P<menuid>[-\w]+)/all_search_options/$', 'all_search_options'),
    url(r'^search/querybuilder/(?P<page>\d+)/(?P<results_per_page>\d+)/(?P<tables_str>\w+)/(?P<where_str>\w+)/(?P<whereis_str>\w+)/(?P<output_str>[:\w]+)/(?P<querystr_str>[\w\.]*)/*$', 'querypage', name="search-querypage"),
    url(r'^search/querybuilder/(?P<tables_str>\w+)/(?P<where_str>\w+)/(?P<whereis_str>\w+)/(?P<output_str>[:\w]+)/(?P<querystr_str>[\w\.]*)/*$', 'query_export', name="search-exportcsv"),
    url(r'^search/phenotypes/$', 'showPhenotypes'),
    url(r'^search/platforms/$', 'showPlatforms'),
    url(r'^search/studies/$', 'showStudies'),
    url(r'^search/qcs/$', 'showQCs'),
    url(r'^search/sources/$', 'showSources'),
    url(r'^search/individuals/$', 'showIndividuals'),
    url(r'^search/samples/$', 'showSamples'),
    
#    url(r'^search/results/$', 'results'),
#    url(r'^search/builder/$', 'builder'),
#    url(r'^search/(?P<individualidentifier_id>\d+)/results/$', 'results'),
#    url(r'^search/(?P<individualidentifier_id>\d+)/builder/results/$', 'builderResults'),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
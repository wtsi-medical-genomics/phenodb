from django.conf.urls import url

from . import views

app_name = 'search'
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^querybuilder/$', views.querybuilder, name='querybuilder'),
    url(r'^querybuilder/(?P<menuid>[-\w]+)/all_json_models/$', views.all_json_models, name='all_json_models'),
    url(r'^querybuilder/(?P<menuid>[-\w]+)/(?P<menuval>[-\w]+)/all_search_options/$', views.all_search_options, name='all_search_options'),
    url(r'^querybuilder/(?P<page>\d+)/(?P<results_per_page>\d+)/*$', views.querypage, name='querypage'),
    url(r'^querybuilder/export/*$', views.query_export, name='exportcsv'),
    url(r'^phenotypes/$', views.showPhenotypes, name='showPhenotypes'),
    url(r'^phenotypes/(?P<phenotype_id>\w+)/data/$', views.getPhenotypePlotData, name='getPhenotypePlotData'),
    url(r'^phenotypes/(?P<phenotype_id>\w+)/$', views.showPhenotypePlot, name='showPhenotypePlot'),
    url(r'^platforms/$', views.showPlatforms, name='showPlatforms'),
    url(r'^studies/$', views.showStudies, name='showStudies'),
    url(r'^qcs/$', views.showQCs, name='showQCs'),
    url(r'^sources/$', views.showSources, name='showSources'),
    url(r'^collections/$', views.showCollections, name='showCollections'),
    url(r'^missing/$', views.showMissing, name='showMissing'),
    url(r'^missing/(?P<study_id>\w+)/$', views.showMissingStudy, name='showMissingStudy'),
    url(r'^individuals/$', views.showIndividuals, name='showIndividuals'),
    url(r'^individuals/data$', views.getIndividualData, name='getIndividualData'),
    url(r'^samples/$', views.showSamples, name='showSamples'),
    url(r'^samples/data$', views.getSampleData, name='getSampleData'),
]
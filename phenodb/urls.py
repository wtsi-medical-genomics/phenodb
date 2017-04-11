"""phenodb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^', include('search.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^admin/', admin.site.urls),
]

# from django.conf.urls import patterns, include, url
# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# from django.contrib import admin

# admin.autodiscover()

# urlpatterns = patterns('search.views',
#     url(r'^search/$', 'home'),
#     url(r'^search/querybuilder/$', 'querybuilder'),
#     url(r'^search/querybuilder/(?P<menuid>[-\w]+)/all_json_models/$', 'all_json_models'),
#     url(r'^search/querybuilder/(?P<menuid>[-\w]+)/(?P<menuval>[-\w]+)/all_search_options/$', 'all_search_options'),
#     url(r'^search/querybuilder/(?P<page>\d+)/(?P<results_per_page>\d+)/*$', 'querypage', name="search-querypage"),
#     url(r'^search/querybuilder/export/*$', 'query_export', name="search-exportcsv"),
#     url(r'^search/phenotypes/$', 'showPhenotypes'),
#     url(r'^search/phenotypes/(?P<phenotype_id>\w+)/data/$', 'getPhenotypePlotData'),
#     url(r'^search/phenotypes/(?P<phenotype_id>\w+)/$', 'showPhenotypePlot'),
#     url(r'^search/platforms/$', 'showPlatforms'),
#     url(r'^search/studies/$', 'showStudies'),
#     url(r'^search/qcs/$', 'showQCs'),
#     url(r'^search/sources/$', 'showSources'),
#     url(r'^search/collections/$', 'showCollections'),
#     url(r'^search/missing/$', 'showMissing'),
#     url(r'^search/missing/(?P<study_id>\w+)/$', 'showMissingStudy'),
#     url(r'^search/individuals/$', 'showIndividuals'),
#     url(r'^search/individuals/data$', 'getIndividualData'),
#     url(r'^search/samples/$', 'showSamples'),
#     url(r'^search/samples/data$', 'getSampleData'),
#     url(r'^admin/', include(admin.site.urls)),
#     url(r'^$', 'home'),
# )

# urlpatterns += staticfiles_urlpatterns()
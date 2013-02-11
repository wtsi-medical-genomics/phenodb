import django_tables2 as tables
from django_tables2.utils import Accessor
from search.models import Platform, Study, QC, Source, Individual, Sample

class PlatformTable(tables.Table):        
    class Meta:
        model  = Platform
        fields = ('platform_name', 'platform_type', 'platform_description')
        attrs  = {'class': 'table table-striped table-bordered'}

class StudyTable(tables.Table):        
    class Meta:
        model  = Study
        fields = ('study_name', 'study_name', 'data_location', 'study_description')         
        attrs  = {'class': 'table table-striped table-bordered'}
        
class QCTable(tables.Table):        
    class Meta:
        model  = QC
        fields = ('qc_name', 'qc_description')         
        attrs  = {'class': 'table table-striped table-bordered'}
        
class SourceTable(tables.Table):        
    class Meta:
        model  = Source
        fields = ('source_name', 'contact_name', 'source_description')         
        attrs  = {'class': 'table table-striped table-bordered'}

class IndividualTable(tables.Table):        
    class Meta:
        model  = Individual
        fields = ('id', 'sex')         
        attrs  = {'class': 'table table-striped table-bordered'}
        
class SampleTable(tables.Table):        
    class Meta:
        model  = Sample
        fields = ('sample_id')         
        attrs  = {'class': 'table table-striped table-bordered'}
        
class CountTable(tables.Table):        
    name  = tables.Column()
    count = tables.Column()
    
    class Meta:         
        attrs = {'class': 'table table-striped table-bordered'}                

class PhenotypeTable(tables.Table):        
    phenotype_name = tables.Column()
    description    = tables.Column()
    values         = tables.LinkColumn('search.views.showPhenotypePlot', args=[Accessor("phenotype_id")])
    total_records  = tables.Column()
    
    class Meta:
        attrs = {'class': 'table table-striped table-bordered'}

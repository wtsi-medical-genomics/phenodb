import django_tables2 as tables
from search.models import Platform, Study, QC, Source, Individual, Sample

class PlatformTable(tables.Table):        
    class Meta:
        model = Platform
        fields = ('platform_name', 'platform_type', 'platform_description')
        attrs = {'class': 'table table-striped table-bordered'}

class StudyTable(tables.Table):        
    class Meta:
        model = Study
        fields = ('study_name', 'study_name', 'data_location', 'study_description')         
        attrs = {'class': 'table table-striped table-bordered'}
        
class QCTable(tables.Table):        
    class Meta:
        model = QC
        fields = ('qc_name', 'qc_description')         
        attrs = {'class': 'table table-striped table-bordered'}
        
class SourceTable(tables.Table):        
    class Meta:
        model = Source
        fields = ('source_name', 'contact_name', 'source_description')         
        attrs = {'class': 'table table-striped table-bordered'}

class IndividualTable(tables.Table):        
    class Meta:
        model = Individual
        fields = ('id', 'sex')         
        attrs = {'class': 'table table-striped table-bordered'}
        
class SampleTable(tables.Table):        
    class Meta:
        model = Sample
        fields = ('sample_id')         
        attrs = {'class': 'table table-striped table-bordered'}
        
class CountTable(tables.Table):        
    name = tables.Column()
    count = tables.Column()
    
    class Meta:         
        attrs = {'class': 'table table-striped table-bordered'}                

class PhenotypeTable(tables.Table):        
    name = tables.Column()
    description = tables.Column()
    currently_held_values = tables.Column()
    not_null_total = tables.Column()
    
    class Meta:
        attrs = {'class': 'table table-striped table-bordered'}

from django.db import models

class PlatformType(models.Model):
    platform_type = models.CharField(max_length=100, unique=True)
    
    def __unicode__(self):
        return self.platform_type
    
class Platform(models.Model):
    platform_name = models.CharField(max_length=100, unique=True)
    platform_type = models.ForeignKey(PlatformType)
    platform_description = models.TextField()
    
    def __unicode__(self):
        return self.platform_name

class PhenotypeType(models.Model):
    phenotype_type = models.CharField(max_length=100, unique=True)
    
    def __unicode__(self):
        return self.phenotype_type

class Phenotype(models.Model):
    phenotype_name = models.CharField(max_length=100, unique=True)
    phenotype_type = models.ForeignKey(PhenotypeType)
    phenotype_description = models.TextField()

    def __unicode__(self):
        return self.phenotype_name
    
class Individual(models.Model):
#    father = models.ForeignKey(Individual)
#    mother = models.ForeignKey(Individual)
    sex = models.SmallIntegerField()
    has_dup = models.BooleanField()
    flagged = models.BooleanField()
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
#class Duplicate(models.Model):
#    individual_1 = models.ForeignKey(Individual)
#    individual_2 = models.ForeignKey(Individual)
#    date_created = models.DateTimeField()
#    last_updated = models.DateTimeField()

class AffectionStatusPhenotypeValue(models.Model):
    phenotype = models.ForeignKey(Phenotype)
    individual = models.ForeignKey(Individual)
    phenotype_value = models.SmallIntegerField()
    flagged = models.BooleanField() 
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    ## phenotype.db_index = True
    
    def __unicode__(self):
        return self.phenotype_value
    
class QualitativePhenotypeValue(models.Model):
    phenotype = models.ForeignKey(Phenotype)
    individual = models.ForeignKey(Individual)
    phenotype_value = models.CharField(max_length=200)
    flagged = models.BooleanField() 
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
    def __unicode__(self):
        return self.phenotype_value

class QuantitiatvePhenotypeValue(models.Model):
    phenotype = models.ForeignKey(Phenotype)
    individual = models.ForeignKey(Individual)
    phenotype_value = models.DecimalField(max_digits=10, decimal_places=2)
    flagged = models.BooleanField() 
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
    def __unicode__(self):
        return self.phenotype_value

class Study(models.Model):
    study_name = models.CharField(max_length=100, unique=True)
    platform = models.ForeignKey(Platform)
    data_location = models.CharField(max_length=200)
    study_description = models.TextField()
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
    def __unicode__(self):
        return self.study_name

class Sample(models.Model):
    individual = models.ForeignKey(Individual)
    sample_id = models.CharField(max_length=100)
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
class StudySamples(models.Model):
    study = models.ForeignKey(Study)
    sample = models.ForeignKey(Sample)
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
class Source(models.Model):
    source_name = models.CharField(max_length=100, unique=True)
    contact_name = models.CharField(max_length=100)
    source_description = models.TextField()
    
    def __unicode__(self):
        return self.source_name

class IndividualIdentifier(models.Model):
    individual = models.ForeignKey(Individual)
    individual_string = models.CharField(max_length=100)
    source = models.ForeignKey(Source)
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
    def __unicode__(self):
        return self.individual_string

class QC(models.Model):
    qc_name = models.CharField(max_length=100, unique=True)
    qc_description = models.TextField()
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
    def __unicode__(self):
        return self.qc_name
    
class SampleQC(models.Model):
    sample = models.ForeignKey(Sample)
    platform = models.ForeignKey(Platform)
    study = models.ForeignKey(Study)
    qc = models.ForeignKey(QC)
    qc_pass = models.BooleanField()
    date_created = models.DateTimeField()
    last_updated = models.DateTimeField()
    
class BulkUpload(models.Model):
    pass    

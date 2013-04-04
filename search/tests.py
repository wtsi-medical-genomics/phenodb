from django.test import TestCase
from search.models import Individual, Source, IndividualIdentifier, IndividualCollection, PhenodbIdentifier, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample, StudySample, Phenotype, PhenotypeType
from django.contrib.auth.models import User
import datetime
from django.db import IntegrityError

## TODO
## test files that contain missing data and check that they die in the correct way 
## test that duplicate sample ids are not added
## test warnings if wrong column headings are used
## test phenotype upload
## test sources upload

class AdminTest(TestCase):
    fixtures = ['search_test_data.json']
    
    def setUp(self):
        ## create an admin user and login
        user = User.objects.create_user('test', 'test@testing.com', password='testy')
        user.is_staff = True
        user.is_activem = True
        user.is_superuser = True
        user.save()
    
    def test_individual_upload(self):
        
        self.client.login(username='test', password='testy')
                
        ## open a test input file
        fh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
        
        ## confirm that the test file contains the data we are expecting to make sure the file has not changed
        ## contains 3 lines
        ## line one == ''
        ## ...
        
        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':fh})
        
        inds = Individual.objects.all()
        self.assertEqual(inds.count(), 8)
        
        self.assertEqual(inds[0].active_id, None)
        self.assertEqual(IndividualIdentifier.objects.get(individual = inds[0]).individual_string, "20")
        self.assertEqual(IndividualIdentifier.objects.get(individual = inds[0]).source.source_name, "OXFORD")
        self.assertEqual(PhenodbIdentifier.objects.get(individual = inds[0]).phenodb_id, "pdb1")
        
        self.assertEqual(AffectionStatusPhenotypeValue.objects.filter(individual=inds[0]).count(), 9)
        self.assertEqual(QualitativePhenotypeValue.objects.filter(individual=inds[0]).count(), 3)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.filter(individual=inds[0]).count(), 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="IBD affection status").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Unrelated control").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Proctitis").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Left-sided").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Extensive").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Colectomy").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_dysplasia/cancer").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Chronic continuous").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_acute fulminant").phenotype_value, 0)
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Disease type").phenotype_value, "Ulcerative Colitis")
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Race").phenotype_value, "White")
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Smoking status").phenotype_value, "No")
        
        
        self.assertEqual(inds[1].active_id, None)
        self.assertEqual(IndividualIdentifier.objects.get(individual = inds[1]).individual_string, "84")
        self.assertEqual(IndividualIdentifier.objects.get(individual = inds[1]).source.source_name, "OXFORD")
        self.assertEqual(PhenodbIdentifier.objects.get(individual = inds[1]).phenodb_id, "pdb2")
        self.assertEqual(IndividualCollection.objects.get(individual = inds[1]).collection.collection_name, "UKIBDGC")
        
        self.assertEqual(AffectionStatusPhenotypeValue.objects.filter(individual=inds[1]).count(), 6)
        self.assertEqual(QualitativePhenotypeValue.objects.filter(individual=inds[1]).count(), 3)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.filter(individual=inds[1]).count(), 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="IBD affection status").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Unrelated control").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Proctitis").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Left-sided").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Extensive").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Colectomy").phenotype_value, 0)        
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Disease type").phenotype_value, "Ulcerative Colitis")
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Race").phenotype_value, "White")
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Smoking status").phenotype_value, "Ex-smoker")
        
        ## check individual sex
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Sex").phenotype_value, 1)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Sex").phenotype_value, 1)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[2],phenotype__phenotype_name="Sex").phenotype_value, 2)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[3],phenotype__phenotype_name="Sex").phenotype_value, 1)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[4],phenotype__phenotype_name="Sex").phenotype_value, 2)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[5],phenotype__phenotype_name="Sex").phenotype_value, 1)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[6],phenotype__phenotype_name="Sex").phenotype_value, 2)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[7],phenotype__phenotype_name="Sex").phenotype_value, 0)
        
    def test_individual_source_unique(self):
        
        ## load the same individual file twice and check that data does not get duplicated
        self.client.login(username='test', password='testy')
                
        ## load a test input file
        fh1 = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':fh1})

        self.assertEqual(Individual.objects.all().count(), 8)
        self.assertEqual(IndividualIdentifier.objects.all().count(), 8)
        self.assertEqual(PhenodbIdentifier.objects.all().count(), 8)
        self.assertEqual(IndividualCollection.objects.all().count(), 7)
        
        ## load the same test input file again
        fh2 = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':fh2})
        
        self.assertEqual(Individual.objects.all().count(), 8)
        self.assertEqual(IndividualIdentifier.objects.all().count(), 8)
        self.assertEqual(PhenodbIdentifier.objects.all().count(), 8)
        self.assertEqual(IndividualCollection.objects.all().count(), 7)
        
    def test_phenodbid_unique(self):
    
        ## test that phenodb ids are unique and raise a integrity error if a duplicate is entered into the database
        self.client.login(username='test', password='testy')
        
        ## create an id
        ind = Individual()                
        ind.date_created = datetime.datetime.now()
        ind.last_updated = datetime.datetime.now()
        ind.save()
        
        ## create the phenodb_id
        pdbId = PhenodbIdentifier()
        pdbId.individual = ind
        pdbId.phenodb_id = u"pdb" + str(ind.pk)
        pdbId.date_created = datetime.datetime.now()
        pdbId.last_updated = datetime.datetime.now()
        pdbId.save()
        
        ## try and insert the same phenodb_id
        pdbId2 = PhenodbIdentifier()
        pdbId2.individual = ind
        pdbId2.phenodb_id = u"pdb" + str(ind.pk)
        pdbId2.date_created = datetime.datetime.now()
        pdbId2.last_updated = datetime.datetime.now()
        pdbId2.save()
        
        self.assertEqual(PhenodbIdentifier.objects.all().count(), 1)
        
    def test_indid_source_unique(self):
        
        ## test that individual ids + sources can not be duplicated
        self.client.login(username='test', password='testy')
        
        ## create an id
        ind = Individual()                
        ind.date_created = datetime.datetime.now()
        ind.last_updated = datetime.datetime.now()
        ind.save()
        
        ## insert the individual identifier
        indId = IndividualIdentifier()
        indId.individual = ind
        indId.individual_string = 'test'                
        indId.source = Source.objects.get(source_name="OXFORD")
        indId.date_created = datetime.datetime.now()
        indId.last_updated = datetime.datetime.now() 
        indId.save()
        
        ## try and insert the same source and individual identifier
        indId2 = IndividualIdentifier()
        indId2.individual = ind
        indId2.individual_string = 'test'                
        indId2.source = Source.objects.get(source_name="OXFORD")
        indId2.date_created = datetime.datetime.now()
        indId2.last_updated = datetime.datetime.now() 
        
        with self.assertRaises(IntegrityError):
            indId2.save()

#    def test_sample_upload(self):
#        
#        self.client.login(username='test', password='testy')
#                
#        ## open a test input files
#        indfh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
#        samplefh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
#        ## load individuals
#        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':indfh})
#        ## load samples
#        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Samples', 'file_to_import':samplefh})
#        
#        samples = Sample.objects.all()
#        self.assertEqual(samples.count(), 8)
#        ## check the id and the ind id of some samples
#        self.assertEqual(samples[0].sample_id, "UC179853")
#        self.assertEqual(samples[0].individual.id, 1)
#        self.assertEqual(samples[1].sample_id, "UC180181")
#        self.assertEqual(samples[1].individual.id, 2)
#        self.assertEqual(samples[7].sample_id, "UC179849")
#        self.assertEqual(samples[7].individual.id, 8)
#        
#    def test_samplestudy_upload(self):    
#        
#        self.client.login(username='test', password='testy')
#        
#        ## open a test input files
#        indfh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
#        samplefh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
#        ## load individuals
#        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':indfh})
#        ## load samples
#        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Samples', 'file_to_import':samplefh})
#
#        studyfh = open('/Users/jm20/work/workspace/phenodb/data/test_sample_study.csv', 'r')
#        ## load samples
#        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'study_samples', 'file_to_import':studyfh})
#        self.assertEqual(StudySample.objects.all().count(), 7)
#    
    def test_add_new_sampleID_on_sampleID(self):
        
        self.client.login(username='test', password='testy')
        
        ## open a test input files
        indfh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
        samplefh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
        ## load individuals
        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':indfh})
        ## load samples
        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Samples', 'file_to_import':samplefh})

        indid2samplefh = open('/Users/jm20/work/workspace/phenodb/data/test_add_new_sampleID_on_sampleID.csv', 'r')
        ## load samples
        print self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'add_sample_on_sample', 'file_to_import':indid2samplefh})
        self.assertEqual(Sample.objects.all().count(), 17)
        
    def test_bulkadd_phenotype_to_individual(self):
        
        ## test that you can bulk upload a file of new/updated phenotypes for existing individuals
        ## centre and centre id or phenodbid?
                
        ## add a new phenotype to match test file
        phenotype = Phenotype()
        phenotype.phenotype_name = "Test"
        phenotype.phenotype_description = "Test description" 
        phenotype.phenotype_type = PhenotypeType.objects.get(phenotype_type="Quantitative")
        phenotype.save()
        
        self.client.login(username='test', password='testy')

        fh = open('/Users/jm20/work/workspace/phenodb/data/test_individual_input.csv', 'r')
        self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':fh})
        
        ## open test input file
        fh = open('/Users/jm20/work/workspace/phenodb/data/test_add_phenotype.csv', 'r')
        print self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'add_phenotype_values', 'file_to_import':fh})
        
        self.assertEqual(QuantitiatvePhenotypeValue.objects.filter(phenotype__phenotype_name="Test").count(), 5)
        
        ## get an individual
        ind1 = IndividualIdentifier.objects.get(individual_string = '20',source__source_name = 'OXFORD')
        ind2 = IndividualIdentifier.objects.get(individual_string = '133',source__source_name = 'OXFORD')
        ind3 = IndividualIdentifier.objects.get(individual_string = '166',source__source_name = 'OXFORD')
        ind4 = IndividualIdentifier.objects.get(individual_string = '190',source__source_name = 'OXFORD')
        ind5 = IndividualIdentifier.objects.get(individual_string = '202',source__source_name = 'OXFORD')
        
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind1).phenotype_value, 1)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind2).phenotype_value, 2)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind3).phenotype_value, 2)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind4).phenotype_value, 3)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind5).phenotype_value, 0)
        
        ## test if existing affection status phenotypes are updated
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind1).phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind2).phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind3).phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind4).phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind5).phenotype_value, 0)
        
        ## test if existing qualitative phenotypes are updated
        self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind1).phenotype_value, "test")
        self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind2).phenotype_value, "test")
        self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind3).phenotype_value, "test")
        self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind4).phenotype_value, "test")
        self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind5).phenotype_value, "test")
        
        ## test if existing quantitative phenotypes are updated
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind1).phenotype_value, 0)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind2).phenotype_value, 0)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind3).phenotype_value, 0)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind4).phenotype_value, 0)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind5).phenotype_value, 0)

        
        
        
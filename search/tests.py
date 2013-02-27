from django.test import TestCase
from search.models import Individual, Source, Collection, IndividualIdentifier, IndividualCollection, PhenodbIdentifier, AffectionStatusPhenotypeValue, QualitativePhenotypeValue, QuantitiatvePhenotypeValue, Sample
from django.contrib.auth.models import User

class AdminTest(TestCase):
    fixtures = ['search_test_data.json']
    
    def test_individual_upload(self):
        
        ## create an admin user and login
        user = User.objects.create_user('test', 'test@testing.com', password='testy')
        user.is_staff = True
        user.is_activem = True
        user.is_superuser = True
        user.save()
        self.client.login(username='test', password='testy')
                
        ## open a test input file
        fh = open('/Users/jm20/work/phenodb/data/test_individual_input.csv', 'r')
        
        ## confirm that the test file contains the data we are expecting to make sure the file has not changed
        ## contains 3 lines
        ## line one == ''
        ## ...
        
        ## test that the view returns the correct status
        response = self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':fh})
#        self.assertEqual(response.status_code, 200)
        
        inds = Individual.objects.all()
        ind = inds[0]
        indId = IndividualIdentifier.objects.get(individual = ind)
        
        self.assertEqual(inds.count(), 8)
        self.assertEqual(ind.active_id, None)
        self.assertEqual(indId.individual_string, "20")
        self.assertEqual(indId.source.source_name, "OXFORD")
        self.assertEqual(PhenodbIdentifier.objects.get(individual = ind).phenodb_id, "pdb1")
#        self.assertEqual(IndividualCollection.objects.get(individual = ind).collection.collection_name, "UKIBDGC")
        
        ## test phenotypes
        self.assertEqual(AffectionStatusPhenotypeValue.objects.filter(individual=ind).count(), 9)
        self.assertEqual(QualitativePhenotypeValue.objects.filter(individual=ind).count(), 3)
        self.assertEqual(QuantitiatvePhenotypeValue.objects.filter(individual=ind).count(), 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="IBD affection status").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="Unrelated control").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="UC_Proctitis").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="UC_Left-sided").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="UC_Extensive").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="UC_Colectomy").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="UC_dysplasia/cancer").phenotype_value, 1)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="UC_Chronic continuous").phenotype_value, 0)
        self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="UC_acute fulminant").phenotype_value, 0)
        
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="Disease type").phenotype_value, "Ulcerative Colitis")
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="Race").phenotype_value, "White")
        self.assertEqual(QualitativePhenotypeValue.objects.get(individual=ind,phenotype__phenotype_name="Smoking status").phenotype_value, "No")
        
    ## test that phenodb id are unique
        
    ## test files that contain missing data and check that they die in the correct way
        
    ## test that duplicate sample ids are not added
        
    ## test warnings if wrong column headings are used

    def test_sample_upload(self):
        
        ## create an admin user and login
        user = User.objects.create_user('test', 'test@testing.com', password='testy')
        user.is_staff = True
        user.is_activem = True
        user.is_superuser = True
        user.save()
        self.client.login(username='test', password='testy')
                
        ## open a test input file
        indfh = open('/Users/jm20/work/phenodb/data/test_individual_input.csv', 'r')
        samplefh = open('/Users/jm20/work/phenodb/data/test_individual_input.csv', 'r')
        
        response = self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Individuals', 'file_to_import':indfh})
        
        response = self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'Samples', 'file_to_import':samplefh})
        
        samples = Sample.objects.all()
        
        self.assertEqual(samples.count(), 8)
        
        sample = samples[0]
        
#        self.assertEqual(ind.active_id, None)
        
        
        
        
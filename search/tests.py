from django.test import TestCase
from .models import *
from django.contrib.auth.models import User
import datetime
from django.db import IntegrityError
from xml.etree import ElementTree as ET
from django.conf import settings
import os
from collections import defaultdict
import csv
from . import phenotype_encoding as pe

## TODO
## test files that contain missing data and check that they die in the correct way 
## test that duplicate sample ids are not added
## test warnings if wrong column headings are used
## test phenotype upload
## test sources upload


def write(filename, listofdicts, keys, sep='\t'):
    with open (filename, 'w') as f:
        f.write(sep.join(keys) + '\n')
        for D in listofdicts:
            line = sep.join([D[k] for k in keys]) + '\n'
            f.write(line)


phenotype_values = [{
    "name": "Sex",
    "type": "Qualitative",
    "description": "Values: 'Male', 'Female', 'M', 'F', '1', '2', 'Unknown', '0'",
}, {
    "name": "Year of birth",
    "type": "Quantitative",
    "description": "Range: 1900 or greater",
}, {
    "name": "IBD affection status",
    "type": "Affection Status",
    "description": "Values: 'Unaffected', 'Affected'",
}, {
    "name": "Disease type",
    "type": "Qualitative",
    "description": "Required if affection equals 'Affected'; otherwise must be left blank; Values: 'Crohn's Disease', 'Ulcerative Colitis', 'Indeterminate', 'Unknown'",
}, {
    "name": "Unrelated control",
    "type": "Affection Status",
    "description": "Indicator for unrelated, healthy controls (1 for controls, 0 otherwise); Those designated as controls should have no family history of IBD.",
}, {
    "name": "Race",
    "type": "Qualitative",
    "description": "Values:'American Indian/Alaskan Native', 'Asian', 'Black/African American', 'Native Hawaiian/Pacific Islander', 'Other', 'Unknown', 'White'",
}, {
    "name": "Smoking status",
    "type": "Qualitative",
    "description": "Smoking status at diagnosis/ascertainment (i.e., within the three months immediately prior); For affected subjects this field represents smoking status at diagnosis of IBD, whereas for unaffected subjects it represents smoking status at time of ascertainment. Note that the possible values differ in these two cases; Values Affected subjects: 'Yes', 'Ex-smoker', 'No', 'Unknown'; Unaffected subjects: 'Current smoker','Ex-smoker','Non-smoker','Unknown'",
}, {
    "name": "Year of diagnosis",
    "type": "Quantitative",
    "description": "Range: 1900 or greater",
}]

sources = [{
    "centre": "PLACE1",
    "contact": "Dave Spears",
    "description": "This place is PLACE1.",
}, {
    "centre": "DORKNEY",
    "contact": "Janet Pears",
    "description": "This place is DORKNEY.",
}]



individuals = '''\
centre,centre_id,Sex,Year of birth,IBD affection status,Disease type,Unrelated control,Race,Smoking status,Year of diagnosis
PLACE1,20,1,,Affected,Ulcerative Colitis,0,White,No,
PLACE1,84,Male,,Affected,Ulcerative Colitis,0,White,Ex-smoker,
PLACE1,133,Female,,Affected,Ulcerative Colitis,0,White,Yes,
PLACE1,166,MALE,,Affected,Ulcerative Colitis,0,White,No,
PLACE1,190,FEMALE,,Affected,Ulcerative Colitis,0,White,Ex-smoker,
PLACE1,202,M,1962,Affected,Crohn's disease,0,White,No,1999
PLACE1,237,F,,Affected,Ulcerative Colitis,0,White,No,
PLACE1,247,other,,Unaffected,Ulcerative Colitis,0,White,Yes,
PLACE1,247,,,Affected,Ulcerative Colitis,0,White,Yes,
DORKNEY,DM02_0721,Male,1966,Affected,Ulcerative Colitis,0,White,No,1978
DORKNEY,DM02_0725,Female,1937,Affected,Ulcerative Colitis,0,White,No,1959
DORKNEY,DM02_0741,Male,1980,Affected,Crohn's disease,0,White,Yes,1908
DORKNEY,DM02_0748,UNKNOWN,1946,Affected,Ulcerative Colitis,0,Other,No,1952
'''

individuals_expected = '''\
centre,centre_id,Sex,Year of birth,IBD affection status,Disease type,Unrelated control,Race,Smoking status,Year of diagnosis
PLACE1,20,Male,,1,ulcerative colitis,0,white,no,
PLACE1,84,Male,,1,ulcerative colitis,0,white,ex-smoker,
PLACE1,133,Female,,1,ulcerative colitis,0,white,yes,
PLACE1,166,Male,,1,ulcerative colitis,0,white,no,
PLACE1,190,Female,,1,ulcerative colitis,0,white,ex-smoker,
PLACE1,202,Male,1962,1,crohn's disease,0,white,no,1999
PLACE1,237,Female,,1,ulcerative colitis,0,white,no,
PLACE1,247,Unknown,,0,ulcerative colitis,0,white,yes,
PLACE1,247,,,0,ulcerative colitis,0,white,yes,
DORKNEY,DM02_0721,Male,1966,1,ulcerative colitis,0,white,no,1978
DORKNEY,DM02_0725,Female,1937,1,ulcerative colitis,0,white,no,1959
DORKNEY,DM02_0741,Male,1980,1,crohn's disease,0,white,yes,1908
DORKNEY,DM02_0748,Unknown,1946,1,ulcerative colitis,0,other,no,1952
'''

class Tests(TestCase):

    @classmethod
    def setUpTestData(cls):
        for phenotypetype in ['Quantitative', 'Qualitative', 'Affection Status']:
            PhenotypeType.objects.create(phenotype_type=phenotypetype)

    def setUp(self):
        settings.MIGRATION_MODULES = {
            'auth': None,
            'contenttypes': None,
            'default': None,
            'sessions': None,
            'core': None,
            'profiles': None,
            'snippets': None,
            'scaffold_templates': None,
        }
        user = User.objects.create_user('test', 'test@testing.com', password='testy')
        user.is_staff = True
        user.is_activem = True
        user.is_superuser = True
        user.save()

        self.client.login(username='test', password='testy')
        testdata = 'search/testdata/'
        
        # load sources
        filepath = os.path.join(testdata, 'sources.tsv')
        write(filepath, sources, ["centre", "contact", "description"])
        with open(filepath) as f:
            self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'sources', 'file_to_import':f, 'file_delimiter': 'tab'})
        
        # load phenotype_values
        filepath = os.path.join(testdata, 'phenotype_values.tsv')
        write(filepath, phenotype_values, ["name", "type", "description"])
        with open(filepath) as f:
            self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'phenotypes', 'file_to_import':f, 'file_delimiter': 'tab'})

        # load individuals
        filepath = os.path.join(testdata, 'individuals.csv')
        with open (filepath, 'w') as f:
            f.write(individuals)
        with open (filepath) as f:
            self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'individuals', 'file_to_import':f, 'file_delimiter': 'comma'})

        # # load individuals
        # with open('search/testdata/test_individual_input.csv') as f:
        #     self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'individuals', 'file_to_import':f, 'file_delimiter': 'comma'})
        
        # #load samples
        # with open('search/testdata/test_individual_input.csv') as f:
        #     self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'samples', 'file_to_import':f, 'file_delimiter': 'comma'})

        # # load individuals again
        # with open('search/testdata/test_individual_input.csv') as f:
        #     self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'individuals', 'file_to_import':f, 'file_delimiter': 'comma'})

        # # load wtccc1 sample study
        # with open('search/testdata/test_sample_study_wtccc1.txt') as f:
        #     self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'study_samples', 'file_to_import':f, 'study_id': 1, 'file_delimiter': 'comma'})
        
        # # load wtccc2 sample study
        # with open('search/testdata/test_sample_study_wtccc2.txt') as f:
        #     self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'study_samples', 'file_to_import':f, 'study_id': 2, 'file_delimiter': 'comma'})


    def test_phenotypes_upload(self):
        self.assertEqual(PhenotypeType.objects.all().count(), 3)

    
#     def test_file_format(self):
#         ## make sure an error is raised and reported to the user in the file format is incorrect
#         #individual input file
#         indfh = open('search/testdata/test_individual_input_bad.csv')
#         response = self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'individuals', 'file_to_import':indfh, 'file_delimiter': 'comma'})
#         indfh.close()
#         self.assertContains(response, "Input file is missing required column(s) 'centre centre_id'", 302)
#         
#         #sample input file
#         samplefh = open('search/testdata/test_individual_input_bad.csv')
#         response = self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'samples', 'file_to_import':samplefh, 'file_delimiter': 'comma'})
#         samplefh.close()
#         self.assertContains(response, "Input file is missing required column(s) 'centre centre_id sample_id'", 302)
        
    def test_sources_upload(self):
        sources = Source.objects.all()
        self.assertEqual(sources.count(), 2)

    def test_phenotypevalues_upload(self):
        self.assertEqual(Phenotype.objects.all().count(), len(phenotype_values))

        types = defaultdict(int)
        for phenotype_value in phenotype_values:
            phenodb_value = Phenotype.objects.get(phenotype_name=phenotype_value['name'])
            types[phenotype_value['type']] += 1
            self.assertEqual(phenodb_value.phenotype_description, phenotype_value['description'])
            self.assertEqual(phenodb_value.phenotype_type.phenotype_type, phenotype_value['type'])

        for t in ['Affection Status', 'Qualitative', 'Quantitative']:
            self.assertEqual(Phenotype.objects.filter(phenotype_type__phenotype_type=t).count(), types[t])


    def test_individual_upload(self):

        self.assertEqual(Individual.objects.all().count(), 12)
        self.assertEqual(PhenodbIdentifier.objects.all().count(), 12)
        self.assertEqual(IndividualIdentifier.objects.all().count(), 12)
        # self.assertEqual(PhenodbIdentifier.objects.all().count(), 12)
        # self.assertEqual(IndividualCollection.objects.all().count(), 11)
        
    #     self.assertEqual(inds[0].active_id, None)
    #     self.assertEqual(IndividualIdentifier.objects.get(individual = inds[0]).individual_string, "20")
    #     self.assertEqual(IndividualIdentifier.objects.get(individual = inds[0]).source.source_name, "PLACE1")
    #     self.assertEqual(PhenodbIdentifier.objects.get(individual = inds[0]).phenodb_id, "pdb1")
          
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.filter(individual=inds[0]).count(), 9)
        
        # Sex
        all_sex = QualitativePhenotypeValue.objects.filter(
            phenotype__phenotype_name='Sex')
        self.assertEqual(all_sex.count(), 12)

        unknowns = QualitativePhenotypeValue.objects.filter(
            phenotype__phenotype_name='Sex',
            phenotype_value='Unknown')
        self.assertEqual(unknowns.count(), 2)

        males = QualitativePhenotypeValue.objects.filter(
            phenotype__phenotype_name='Sex',
            phenotype_value='Male')
        self.assertEqual(males.count(), 6)

        females = QualitativePhenotypeValue.objects.filter(
            phenotype__phenotype_name='Sex',
            phenotype_value='Female')
        self.assertEqual(females.count(), 4)

        reader = csv.DictReader(individuals_expected.split('\n'))
        for i in reader:
            # Does the centre/source exist?
            s = Source.objects.filter(source_name=i['centre'])
            if not s:
                self.assertEqual(i['centre'], 'TEST')
                continue
            ind_ident = IndividualIdentifier.objects.get(
                individual_string=i['centre_id'],
                source__source_name=i['centre'])
            individual = ind_ident.individual
            for k, v in i.items():
                if not v:
                    continue
                if k in ['centre', 'centre_id']:
                    continue
                # Determine the phenotype table
                filtered_phenotype = list(filter(lambda d: d['name'] == k, phenotype_values))
                phenotypetype = filtered_phenotype[0]['type']
                # phenotype_type = PhenotypeType.objects.get(phenotype_type=phenotype_type)
                if phenotypetype == 'Affection Status':
                    table = AffectionStatusPhenotypeValue
                    v = int(v)
                if phenotypetype == 'Qualitative':
                    table = QualitativePhenotypeValue
                if phenotypetype == 'Quantitative':
                    table = QuantitiatvePhenotypeValue
                    v = int(v)
                # print(k, i['centre_id'], i['centre'])
                p = table.objects.get(
                    phenotype__phenotype_name=k,
                    individual=individual)
                self.assertEqual(p.phenotype_value, v)




    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.filter(individual=inds[0]).count(), 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="IBD affection status").phenotype_value, 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Unrelated control").phenotype_value, 0)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Proctitis").phenotype_value, 0)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Left-sided").phenotype_value, 0)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Extensive").phenotype_value, 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Colectomy").phenotype_value, 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_dysplasia/cancer").phenotype_value, 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_Chronic continuous").phenotype_value, 0)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="UC_acute fulminant").phenotype_value, 0)
    #     self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Disease type").phenotype_value, "Ulcerative Colitis")
    #     self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Race").phenotype_value, "White")
    #     self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Smoking status").phenotype_value, "No")
          
    #     self.assertEqual(inds[1].active_id, None)
    #     self.assertEqual(IndividualIdentifier.objects.filter(individual = inds[1])[0].individual_string, "84")
    #     self.assertEqual(IndividualIdentifier.objects.filter(individual = inds[1])[1].individual_string, "84_b")
    #     self.assertEqual(IndividualIdentifier.objects.filter(individual = inds[1])[0].source.source_name, "PLACE1")
    #     self.assertEqual(IndividualIdentifier.objects.filter(individual = inds[1])[1].source.source_name, "PLACE1")
    #     self.assertEqual(PhenodbIdentifier.objects.get(individual = inds[1]).phenodb_id, "pdb2")
    #     self.assertEqual(IndividualCollection.objects.get(individual = inds[1]).collection.collection_name, "UKIBDGC")
          
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.filter(individual=inds[1]).count(), 6)
    #     self.assertEqual(QualitativePhenotypeValue.objects.filter(individual=inds[1]).count(), 3)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.filter(individual=inds[1]).count(), 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="IBD affection status").phenotype_value, 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Unrelated control").phenotype_value, 0)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Proctitis").phenotype_value, 1)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Left-sided").phenotype_value, 0)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Extensive").phenotype_value, 0)
    #     self.assertEqual(AffectionStatusPhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="UC_Colectomy").phenotype_value, 0)        
    #     self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Disease type").phenotype_value, "Ulcerative Colitis")
    #     self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Race").phenotype_value, "White")
    #     self.assertEqual(QualitativePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Smoking status").phenotype_value, "Ex-smoker")
          
    #     ## check individual sex
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[0],phenotype__phenotype_name="Sex").phenotype_value, 1)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[1],phenotype__phenotype_name="Sex").phenotype_value, 1)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[2],phenotype__phenotype_name="Sex").phenotype_value, 2)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[3],phenotype__phenotype_name="Sex").phenotype_value, 1)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[4],phenotype__phenotype_name="Sex").phenotype_value, 2)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[5],phenotype__phenotype_name="Sex").phenotype_value, 1)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[6],phenotype__phenotype_name="Sex").phenotype_value, 2)
    #     self.assertEqual(QuantitiatvePhenotypeValue.objects.get(individual=inds[7],phenotype__phenotype_name="Sex").phenotype_value, 0)
          
    # def test_individual_source_unique(self):
    
    #     ## load the same test input file again
    #     fh2 = open('search/testdata/test_individual_input.csv')
    #     self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'individuals', 'file_to_import':fh2, 'file_delimiter': 'comma'})
    #     fh2.close()
          
    #     self.assertEqual(Individual.objects.all().count(), 12)
    #     self.assertEqual(IndividualIdentifier.objects.all().count(), 13)
    #     self.assertEqual(PhenodbIdentifier.objects.all().count(), 12)
    #     self.assertEqual(IndividualCollection.objects.all().count(), 11)
          
    # def test_phenodbid_unique(self):
      
    #     ## test that phenodb ids are unique and raise a integrity error if a duplicate is entered into the database
    #     ind = Individual.objects.get(id=1)
        
    #     pdbId = PhenodbIdentifier()
    #     pdbId.individual = ind
    #     pdbId.phenodb_id = u"pdb" + str(ind.pk)
    #     pdbId.date_created = datetime.datetime.now()
    #     pdbId.last_updated = datetime.datetime.now()
    #     pdbId.save()
        
    #     self.assertEqual(PhenodbIdentifier.objects.all().count(), 12)
          
    # def test_indid_source_unique(self):
          
    #     ## test that individual ids + sources can not be duplicated
    #     ## create an id
    #     ind = Individual()                
    #     ind.date_created = datetime.datetime.now()
    #     ind.last_updated = datetime.datetime.now()
    #     ind.save()
          
    #     ## insert the individual identifier
    #     indId = IndividualIdentifier()
    #     indId.individual = ind
    #     indId.individual_string = 'test'                
    #     indId.source = Source.objects.get(source_name="PLACE1")
    #     indId.date_created = datetime.datetime.now()
    #     indId.last_updated = datetime.datetime.now() 
    #     indId.save()
          
    #     ## try and insert the same source and individual identifier
    #     indId2 = IndividualIdentifier()
    #     indId2.individual = ind
    #     indId2.individual_string = 'test'                
    #     indId2.source = Source.objects.get(source_name="PLACE1")
    #     indId2.date_created = datetime.datetime.now()
    #     indId2.last_updated = datetime.datetime.now() 
          
    #     with self.assertRaises(IntegrityError):
    #         indId2.save()
  
#     def test_sample_upload(self):
          
#         samples = Sample.objects.all()
#         self.assertEqual(samples.count(), 12)
#         ## check the id and the ind id of some samples
#         self.assertEqual(samples[0].sample_id, "UC179853")
#         self.assertEqual(samples[0].individual.id, 1)
#         self.assertEqual(samples[1].sample_id, "UC180181")
#         self.assertEqual(samples[1].individual.id, 2)
#         self.assertEqual(samples[7].sample_id, "UC179849")
#         self.assertEqual(samples[7].individual.id, 8)
          
#     def test_samplestudy_upload(self):    
  
#         self.assertEqual(StudySample.objects.filter(study__study_name='WTCCC1').count(), 8)
#         self.assertEqual(StudySample.objects.filter(study__study_name='WTCCC2').count(), 4)
        
#         ## check that missing samples are entered in the missing samples table
#         self.assertEqual(MissingSampleID.objects.all().count(), 2)
        
#         ## check that after adding the samples they are removed from the table
#         samplefh = open('search/testdata/test_missing_samples.csv')
#         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'samples', 'file_to_import':samplefh, 'file_delimiter': 'comma'})
#         samplefh.close()
#         self.assertEqual(MissingSampleID.objects.all().count(), 0)
        
#         ## check that the samples are also added to the studies they belong
#         self.assertEqual(StudySample.objects.filter(study__study_name='WTCCC1').count(), 10)
         
#     def test_add_new_sampleID_on_sampleID_csv(self):          
        
#         indid2samplefh = open('search/testdata/test_add_new_sampleID_on_sampleID.csv')
#         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'add_sample_on_sample', 'file_to_import':indid2samplefh, 'file_delimiter': 'comma'})
#         indid2samplefh.close()
        
#         self.assertEqual(Sample.objects.all().count(), 21)

#     def test_add_new_sampleID_on_sampleID_tsv(self):          
        
#         indid2samplefh = open('search/testdata/test_add_new_sampleID_on_sampleID.tsv')
#         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'add_sample_on_sample', 'file_to_import':indid2samplefh, 'file_delimiter': 'tab'})
#         indid2samplefh.close()
        
#         self.assertEqual(Sample.objects.all().count(), 21)
        
#     def test_bulkadd_phenotype_to_individual(self):
          
#         ## test that you can bulk upload a file of new/updated phenotypes for existing individuals
#         ## centre and centre id or phenodbid?
                  
#         ## add a new phenotype to match test file
#         phenotype = Phenotype()
#         phenotype.phenotype_name = "Test"
#         phenotype.phenotype_description = "Test description" 
#         phenotype.phenotype_type = PhenotypeType.objects.get(phenotype_type="Quantitative")
#         phenotype.save()
          
#         ## open test input file
#         fh = open('search/testdata/test_add_phenotype.csv')
#         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'add_phenotype_values', 'file_to_import':fh, 'file_delimiter': 'comma'})
#         fh.close()
          
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.filter(phenotype__phenotype_name="Test").count(), 5)
          
#         ## get an individual
#         ind1 = IndividualIdentifier.objects.get(individual_string = '20',source__source_name = 'PLACE1')
#         ind2 = IndividualIdentifier.objects.get(individual_string = '133',source__source_name = 'PLACE1')
#         ind3 = IndividualIdentifier.objects.get(individual_string = '166',source__source_name = 'PLACE1')
#         ind4 = IndividualIdentifier.objects.get(individual_string = '190',source__source_name = 'PLACE1')
#         ind5 = IndividualIdentifier.objects.get(individual_string = '202',source__source_name = 'PLACE1')
          
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind1).phenotype_value, 1)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind2).phenotype_value, 2)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind3).phenotype_value, 2)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind4).phenotype_value, 3)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Test", individual=ind5).phenotype_value, 0)
          
#         ## test if existing affection status phenotypes are updated
#         self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind1).phenotype_value, 0)
#         self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind2).phenotype_value, 0)
#         self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind3).phenotype_value, 0)
#         self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind4).phenotype_value, 0)
#         self.assertEqual(AffectionStatusPhenotypeValue.objects.get(phenotype__phenotype_name="IBD affection status", individual=ind5).phenotype_value, 0)
          
#         ## test if existing qualitative phenotypes are updated
#         self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind1).phenotype_value, "test")
#         self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind2).phenotype_value, "test")
#         self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind3).phenotype_value, "test")
#         self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind4).phenotype_value, "test")
#         self.assertEqual(QualitativePhenotypeValue.objects.get(phenotype__phenotype_name="Disease type", individual=ind5).phenotype_value, "test")
          
#         ## test if existing quantitative phenotypes are updated
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind1).phenotype_value, 0)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind2).phenotype_value, 0)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind3).phenotype_value, 0)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind4).phenotype_value, 0)
#         self.assertEqual(QuantitiatvePhenotypeValue.objects.get(phenotype__phenotype_name="Sex", individual=ind5).phenotype_value, 0)
         
#     def test_bulkadd_sampleQC(self):
         
#         self.client.login(username='test', password='testy')
        
#         # add qc
#         qc = QC()
#         qc.qc_name = 'test qc'
#         qc.qc_description = 'dummy qc for tesing'
#         qc.date_created = datetime.datetime.now()
#         qc.last_updated = datetime.datetime.now()
#         qc.save()
        
#         fh = open('search/testdata/test_upload_sample_qc.txt')
#         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'sample_qc', 'file_to_import':fh, 'file_delimiter': 'tab', 'study_id': 1, 'qc_id': 1})
#         fh.close()
        
#         self.assertEqual(SampleQC.objects.all().count(), 8)
#         self.assertEqual(SampleQC.objects.filter(qc_pass=True).count(), 4)
#         self.assertEqual(SampleQC.objects.filter(qc_pass=False).count(), 4)        
        

# # class QueryTest(TestCase):
      
# #     ## TODO:create a fixture with individual and sample data
# #     ## for now load some individuals and samples using admin scripts
      
# #     # fixtures = ['phenodb.json']
      
# #     def setUp(self):
# #         ## create an admin user and login
# #         user = User.objects.create_user('test', 'test@testing.com', password='testy')
# #         user.is_staff = True
# #         user.is_activem = True
# #         user.is_superuser = True
# #         user.save()
        

# #         self.client.login(username='test', password='testy')
# #         # load individuals
# #         indfh = open('search/testdata/test_individual_input.csv')
# #         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'individuals', 'file_to_import':indfh, 'file_delimiter': 'comma'})
# #         indfh.close()
# #         #load samples
# #         samplefh = open('search/testdata/test_individual_input.csv')
# #         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'samples', 'file_to_import':samplefh, 'file_delimiter': 'comma'})
# #         samplefh.close()
# #         # load wtccc1 sample study
# #         studyfh1 = open('search/testdata/test_sample_study_wtccc1.txt')
# #         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'study_samples', 'file_to_import':studyfh1, 'study_id': 1, 'file_delimiter': 'comma'})
# #         studyfh1.close()
# #         # load wtccc2 sample study
# #         studyfh2 = open('search/testdata/test_sample_study_wtccc2.txt')
# #         self.client.post('/admin/search/bulkupload/add/', {'import_data_type': 'study_samples', 'file_to_import':studyfh2, 'study_id': 2, 'file_delimiter': 'comma'})
# #         studyfh2.close()   
      
#     def test_query_builder(self):
  
#         # get the phenotype primary key first 
#         ibd_affection_status = Phenotype.objects.get(phenotype_name="IBD affection status")
#         sex                  = Phenotype.objects.get(phenotype_name="Sex")
#         yob                  = Phenotype.objects.get(phenotype_name="Year of birth")
#         disease_type         = Phenotype.objects.get(phenotype_name="Disease type")
        
#         PLACE1    = Source.objects.get(source_name = "PLACE1")
#         DORKNEY = Source.objects.get(source_name="DORKNEY")
        
#         wtccc1 = Study.objects.get(study_name="WTCCC1")
#         wtccc2 = Study.objects.get(study_name="WTCCC2")
        
#         affy500k = Platform.objects.get(platform_name="Affy500K")
#         affy6    = Platform.objects.get(platform_name="Affy6.0")
        
  
# #        single phenotype
#         response = self.client.post('/search/querybuilder/', {'from': 'phenotype', 'where': ibd_affection_status.pk, 'is': 'true', 'searchIn': 'all', 'output': 'PhenodbID', 'andor': 'and'})
#         self.assertEqual(response.context['count'], 12)
# #        null queries
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype'], 'where': [sex.pk], 'is': ['notnull'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or']})
#         self.assertEqual(response.context['count'], 12)
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype'], 'where': [sex.pk], 'is': ['isnull'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or']})
#         self.assertEqual(response.context['message'], "Sorry your query didn't return any results, please try another query.")
# #        numerical query
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype'], 'where': [yob.pk], 'is': ['gt'], 'querystr': ['1960'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and']})
#         self.assertEqual(response.context['count'], 3)
# #        multiple phenotypes and
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype','phenotype'], 'where': [ibd_affection_status.pk, disease_type.pk], 'is': ['true','eq'], 'querystr': ['Ulcerative Colitis'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','and']})
#         self.assertEqual(response.context['count'], 10)
# #        multiple phenotypes or
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype','phenotype'], 'where': [ibd_affection_status.pk, disease_type.pk], 'is': ['true','eq'], 'querystr': ['Ulcerative Colitis'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or','and']})
#         self.assertEqual(response.context['count'], 12)
  
# #        user list, single phenotye, source_ids+source        
#         sourceIDsfh = open('search/testdata/test_search_individual_source_ids.txt')
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype'], 'where': [ibd_affection_status.pk], 'is': ['true'], 'searchIn': 'userlist', 'individual_file': sourceIDsfh, 'output': ['PhenodbID'], 'andor': ['and']})
#         self.assertEqual(response.context['count'], 3)
# #        user list, single phenotye, phenodb ids
#         phenoIDsfh = open('search/testdata/test_search_individual_phenodb_ids.txt')
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype'], 'where': [ibd_affection_status.pk], 'is': ['true'], 'searchIn': 'userlist', 'individual_file': phenoIDsfh, 'output': ['PhenodbID'], 'andor': ['and']})
#         self.assertEqual(response.context['count'], 5)
# #        user list, multiple phenotyes, and
#         sourceIDsfh = open('search/testdata/test_search_individual_source_ids.txt')
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype','phenotype'], 'where': [ibd_affection_status.pk, disease_type.pk], 'is': ['true','eq'], 'querystr': ['ulcerative colitis'], 'searchIn': 'userlist', 'individual_file': sourceIDsfh, 'output': ['PhenodbID'], 'andor': ['and','and']})
#         self.assertEqual(response.context['count'], 2)
# #        user list, multiple phenotyes, or
#         sourceIDsfh = open('search/testdata/test_search_individual_source_ids.txt')
#         response = self.client.post('/search/querybuilder/', {'from': ['phenotype','phenotype'], 'where': [disease_type.pk, disease_type.pk], 'is': ['eq','eq'], 'querystr': ['ulcerative colitis','crohn\'s disease'], 'searchIn': 'userlist', 'individual_file': sourceIDsfh, 'output': ['PhenodbID'], 'andor': ['or','and']})
#         self.assertEqual(response.context['count'], 3)
  
# #        single source
#         response = self.client.post('/search/querybuilder/', {'from': 'source', 'where': PLACE1.pk, 'is': 'true', 'searchIn': 'all', 'output': 'PhenodbID', 'andor': 'and'})
#         self.assertEqual(response.context['count'], 8)
# #        multiple source and
#         response = self.client.post('/search/querybuilder/', {'from': ['source','source'], 'where': [PLACE1.pk, DORKNEY.pk], 'is': ['true','true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','and']})
#         self.assertEqual(response.context['message'], "Sorry your query didn't return any results, please try another query.")
# #        multiple source or
#         response = self.client.post('/search/querybuilder/', {'from': ['source','source'], 'where': [PLACE1.pk, DORKNEY.pk], 'is': ['true','true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or','or']})
#         self.assertEqual(response.context['count'], 12)
  
# #        single study
#         response = self.client.post('/search/querybuilder/', {'from': ['study'], 'where': [wtccc1.pk], 'is': ['true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and']})
#         self.assertEqual(response.context['count'], 8)
# #        multiple studies and
#         response = self.client.post('/search/querybuilder/', {'from': ['study','study'], 'where': [wtccc1.pk, wtccc2.pk], 'is': ['true','true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','and']})
#         self.assertEqual(response.context['message'], "Sorry your query didn't return any results, please try another query.")
# #        multiple studies or 
#         response = self.client.post('/search/querybuilder/', {'from': ['study','study'], 'where': [wtccc1.pk, wtccc2.pk], 'is': ['true','true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or','or']})
#         self.assertEqual(response.context['count'], 12)
# #         samples not in a study
#         response = self.client.post('/search/querybuilder/', {'from': ['study'], 'where': [wtccc1.pk], 'is': ['false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or']})
#         self.assertEqual(response.context['count'], 4)
# #        multiple studies not + and
#         response = self.client.post('/search/querybuilder/', {'from': ['study','study'], 'where': [wtccc1.pk, wtccc2.pk], 'is': ['false','false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','and']})
#         self.assertEqual(response.context['message'], "Sorry your query didn't return any results, please try another query.")
# #        multiple studies not + or 
#         response = self.client.post('/search/querybuilder/', {'from': ['study','study'], 'where': [wtccc1.pk, wtccc2.pk], 'is': ['false','false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or','or']})
#         self.assertEqual(response.context['count'], 12)
# #         in one study and not in another
#         response = self.client.post('/search/querybuilder/', {'from': ['study','study'], 'where': [wtccc1.pk, wtccc2.pk], 'is': ['true','false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','or']})
#         self.assertEqual(response.context['count'], 8)
          
# #        single platform
#         response = self.client.post('/search/querybuilder/', {'from': ['platform'], 'where': [affy6.pk], 'is': ['true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and']})
#         self.assertEqual(response.context['count'], 8)
# #        multiple platforms and
#         response = self.client.post('/search/querybuilder/', {'from': ['platform','platform'], 'where': [affy6.pk, affy500k.pk], 'is': ['true','true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','and']})
#         self.assertEqual(response.context['message'], "Sorry your query didn't return any results, please try another query.")
# #        multiple platforms or 
#         response = self.client.post('/search/querybuilder/', {'from': ['platform','platform'], 'where': [affy6.pk, affy500k.pk], 'is': ['true','true'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or','or']})
#         self.assertEqual(response.context['count'], 12)
# #         samples not run on a platform
#         response = self.client.post('/search/querybuilder/', {'from': ['platform'], 'where': [affy6.pk], 'is': ['false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and']})
#         self.assertEqual(response.context['count'], 4)
# #        multiple platforms not + and
#         response = self.client.post('/search/querybuilder/', {'from': ['platform','platform'], 'where': [affy6.pk, affy500k.pk], 'is': ['false','false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','and']})
#         self.assertEqual(response.context['message'], "Sorry your query didn't return any results, please try another query.")
# #        multiple platforms not + or 
#         response = self.client.post('/search/querybuilder/', {'from': ['platform','platform'], 'where': [affy6.pk, affy500k.pk], 'is': ['false','false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['or','or']})
#         self.assertEqual(response.context['count'], 12)        
# #         run on one platform and not another
#         response = self.client.post('/search/querybuilder/', {'from': ['platform','platform'], 'where': [affy6.pk, affy500k.pk], 'is': ['true','false'], 'searchIn': 'all', 'output': ['PhenodbID'], 'andor': ['and','or']})
#         self.assertEqual(response.context['count'], 8)
  
# #        search using sample ids only
#         sampleIDsfh = open('search/testdata/test_search_sample_ids.txt')
#         response = self.client.post('/search/querybuilder/', {'from': ['message'], 'where': [''], 'is': [''], 'searchIn': 'userlist', 'individual_file': sampleIDsfh, 'output': ['PhenodbID'], 'andor': ['and']})
#         self.assertEqual(response.context['count'], 12)
# #        test ignoring case on ind/sample id searches
 
# #        output file
     
#     def parse_html_table(self, html_table):
         
# #        results_table_html = response.context['tablehtml']
# #        results_table = self.parse_html_table(results_table_html)
         
#         table = ET.XML(html_table)
#         rows = iter(table)
#         headers = [col.text for col in next(rows)]
         
#         parsed_rows = []
         
#         for row in rows:            
#             values = [col.text for col in row]
#             parsed_rows.append(dict(zip(headers, values)))
         
#         return parsed_rows

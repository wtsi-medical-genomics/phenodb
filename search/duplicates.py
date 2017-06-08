from .models import IndividualIdentifier, Phenotype, Individual, Sample, Source
from collections import defaultdict

def get_duplicate_sampleIDs():
    samples = Sample.objects.all().select_related('individual')
    individualidentifiers = IndividualIdentifier.objects.all().select_related('source')

    duplicates = defaultdict(list)

    samples2individuals = defaultdict(set)
    individuals2samples = defaultdict(set)
    for sample in samples:
        samples2individuals[sample.sample_id].add(sample.individual)
        individuals2samples[sample.individual_id].add(sample.sample_id)

    for sample, individuals in samples2individuals.items():
        if len(individuals) == 1:
            continue
        individualids = set([x.id for x in individuals])
        if len(individualids) == 1:
            continue
        individualids = tuple(sorted(individualids))
        if individualids in duplicates:
            continue
        
        for individual in individuals:
            queryset = IndividualIdentifier.objects.filter(individual=individual)
            result = defaultdict(set)
            for query in queryset:
                result[query.source.source_name].add(query.individual_string)
            ids_sources = {}
            for k,v in result.items():
                ids_sources[k] = ', '.join(sorted(v))
            
            sample_ids = ', '.join(sorted(individuals2samples[individual.id]))
            duplicates[individualids].append({
                'phenodbid': f'pdb{individual.id}',
                'date': individual.date_created,
                'individual_identifier_sources': ids_sources,
                'sample_ids': sample_ids,
            })

    return duplicates
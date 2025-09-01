'EOF'
#!/usr/bin/env python3
from collections import defaultdict

# Read OTU abundance data
otu_abundance = {}
samples = []
with open('results/vsearch_analysis/otu_table.txt', 'r') as f:
    header = f.readline().strip().split('\t')
    samples = header[1:]
    for line in f:
        parts = line.strip().split('\t')
        otu_id = parts[0]
        counts = [int(x) for x in parts[1:]]
        otu_abundance[otu_id] = dict(zip(samples, counts))

# Read corrected taxonomy
otu_taxonomy = {}
with open('results/vsearch_analysis/fixed_cluster_taxonomy.txt', 'r') as f:
    f.readline()
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 2:
            otu_id = parts[0]
            taxonomy = parts[1]
            otu_taxonomy[otu_id] = taxonomy

# Aggregate by genus
genus_counts = defaultdict(lambda: defaultdict(int))
total_assigned = defaultdict(int)

for otu_id, abundance in otu_abundance.items():
    if otu_id in otu_taxonomy:
        taxonomy = otu_taxonomy[otu_id]
        tax_levels = taxonomy.split(';')
        
        genus = 'Unknown'
        for level in tax_levels:
            if 'D_5__' in level:
                genus = level.split('D_5__')[1].strip()
                break
        
        for sample in samples:
            genus_counts[genus][sample] += abundance[sample]
            total_assigned[sample] += abundance[sample]

print(f'Total assigned reads per sample: {dict(total_assigned)}')
print(f'Found {len(genus_counts)} genera')

# Write final summary
with open('results/vsearch_analysis/corrected_genus_summary.txt', 'w') as f:
    f.write('Genus\t' + '\t'.join(samples) + '\tTotal\tPercent_of_assigned\n')
    
    genus_totals = {genus: sum(counts.values()) for genus, counts in genus_counts.items()}
    total_all_assigned = sum(total_assigned.values())
    
    for genus, total in sorted(genus_totals.items(), key=lambda x: x[1], reverse=True):
        counts = [str(genus_counts[genus][sample]) for sample in samples]
        percent = total/total_all_assigned*100 if total_all_assigned > 0 else 0
        f.write(f'{genus}\t' + '\t'.join(counts) + f'\t{total}\t{percent:.1f}\n')

print('Final genus summary completed')

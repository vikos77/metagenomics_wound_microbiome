'EOF'
#!/usr/bin/env python3
import sys
from collections import defaultdict

# Read cluster file and build OTU table
sample_otu_counts = defaultdict(lambda: defaultdict(int))
otu_names = {}

with open('results/vsearch_analysis/clusters.uc', 'r') as f:
    for line in f:
        if line.startswith('H') or line.startswith('S'):  # Hit or Seed (centroid)
            parts = line.strip().split('\t')
            otu_id = parts[1]
            seq_name = parts[8]
            sample_id = seq_name.split('.')[0]
            
            # Extract abundance from sequence name
            if ';size=' in seq_name:
                abundance = int(seq_name.split(';size=')[1])
            else:
                abundance = 1
            
            sample_otu_counts[sample_id][otu_id] += abundance
            
            if line.startswith('S'):  # Store OTU name
                otu_names[otu_id] = seq_name

# Write OTU table
with open('results/vsearch_analysis/otu_table.txt', 'w') as f:
    samples = sorted(sample_otu_counts.keys())
    all_otus = sorted(set(otu for sample_otus in sample_otu_counts.values() for otu in sample_otus.keys()))
    
    # Header
    f.write('OTU_ID\t' + '\t'.join(samples) + '\n')
    
    # Data rows
    for otu in all_otus:
        counts = [str(sample_otu_counts[sample][otu]) for sample in samples]
        f.write(f'OTU_{otu}\t' + '\t'.join(counts) + '\n')

print('OTU table created successfully')

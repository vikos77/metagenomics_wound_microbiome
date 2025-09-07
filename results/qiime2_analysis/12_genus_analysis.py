#!/usr/bin/env python3

# Read the genus table without external dependencies
genus_summary = {}
samples = []

with open('exported_genus_table/genus_table.tsv', 'r') as f:
    lines = f.readlines()

# Get sample names from header (skip comment line)
header_line = lines[1].strip().split('\t')
samples = header_line[1:]  # Skip the '#OTU ID' column

# Process each taxonomy line
for line in lines[2:]:  # Skip both comment and header lines
    parts = line.strip().split('\t')
    full_taxonomy = parts[0]
    counts = [float(x) for x in parts[1:]]
    
    # Extract genus from taxonomy string
    genus = 'Unknown'
    tax_levels = full_taxonomy.split(';')
    for level in tax_levels:
        if level.startswith('D_5__'):
            genus = level.replace('D_5__', '').strip()
            break
    
    # If no genus found, try family level
    if genus == 'Unknown' or genus == '':
        for level in tax_levels:
            if level.startswith('D_4__'):
                genus = level.replace('D_4__', '').strip() + ' (family)'
                break
    
    # Add to summary
    if genus not in genus_summary:
        genus_summary[genus] = [0.0] * len(samples)
    
    for i, count in enumerate(counts):
        genus_summary[genus][i] += count

# Calculate totals and write summary
sample_totals = [sum(genus_summary[genus][i] for genus in genus_summary) for i in range(len(samples))]
total_all = sum(sample_totals)

# Sort by total abundance
genus_items = list(genus_summary.items())
genus_items.sort(key=lambda x: sum(x[1]), reverse=True)

# Write results
with open('qiime2_genus_summary.txt', 'w') as f:
    f.write('Genus\t' + '\t'.join(samples) + '\tTotal\tPercent\n')
    
    for genus, counts in genus_items:
        total = sum(counts)
        percent = total/total_all*100 if total_all > 0 else 0
        counts_str = '\t'.join([f'{int(c)}' for c in counts])
        f.write(f'{genus}\t{counts_str}\t{int(total)}\t{percent:.1f}\n')

print(f'QIIME2 genus summary created with {len(genus_summary)} genera')
print(f'Total reads analyzed: {int(total_all)}')
print(f'Sample totals: {[int(x) for x in sample_totals]}')


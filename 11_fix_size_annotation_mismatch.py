'EOF'
#!/usr/bin/env python3
# Create base name to cluster mapping (ignoring size annotations)
base_to_cluster = {}
with open('results/vsearch_analysis/clusters.uc', 'r') as f:
    for line in f:
        if line.startswith('S'):  # Centroid sequences
            parts = line.strip().split('\t')
            cluster_num = parts[1]
            full_seq_name = parts[8]
            # Extract base name without size annotation
            base_name = full_seq_name.split(';size=')[0]
            base_to_cluster[base_name] = f'OTU_{cluster_num}'

print(f'Created base name mappings for {len(base_to_cluster)} clusters')

# Map BLAST results to clusters using base names
cluster_taxonomy = {}
with open('results/vsearch_analysis/taxonomy_assignments_fixed.txt', 'r') as f:
    f.readline()  # Skip header
    for line in f:
        parts = line.strip().split('\t')
        blast_seq_name = parts[0]
        taxonomy = parts[3]
        
        # Extract base name from BLAST sequence name
        base_name = blast_seq_name.split(';size=')[0]
        
        if base_name in base_to_cluster:
            cluster_id = base_to_cluster[base_name]
            cluster_taxonomy[cluster_id] = taxonomy

print(f'Successfully mapped taxonomy for {len(cluster_taxonomy)} clusters')

# Write the corrected mapping
with open('results/vsearch_analysis/fixed_cluster_taxonomy.txt', 'w') as f:
    f.write('OTU_ID\tTaxonomy\n')
    for cluster_id, taxonomy in sorted(cluster_taxonomy.items(), key=lambda x: int(x[0].split('_')[1])):
        f.write(f'{cluster_id}\t{taxonomy}\n')

print('Fixed taxonomy mapping written')

'EOF'
#!/usr/bin/env python3
# Read SILVA taxonomy file
silva_taxonomy = {}
with open('results/databases/SILVA_132_QIIME_release/taxonomy/16S_only/97/taxonomy_7_levels.txt', 'r') as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 2:
            seq_id = parts[0]
            taxonomy = parts[1]
            silva_taxonomy[seq_id] = taxonomy

print(f'Loaded taxonomy for {len(silva_taxonomy)} SILVA sequences')

# Assign taxonomy to BLAST results
with open('results/vsearch_analysis/taxonomy_assignments_fixed.txt', 'w') as out:
    out.write('OTU_ID\tSILVA_ID\tPercent_Identity\tTaxonomy\n')
    
    with open('results/vsearch_analysis/blast_results.txt', 'r') as blast:
        for line in blast:
            parts = line.strip().split('\t')
            otu_id = parts[0]
            silva_id = parts[1]
            identity = parts[2]
            
            # Get taxonomy for this SILVA sequence
            taxonomy = silva_taxonomy.get(silva_id, 'Unassigned')
            
            out.write(f'{otu_id}\t{silva_id}\t{identity}\t{taxonomy}\n')

print('Taxonomy assignments written')

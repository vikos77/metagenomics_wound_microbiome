'EOF'
#!/usr/bin env python3
# Calculate assignment statistics
total_reads_all = 0
total_reads_assigned = 0

# Read OTU abundances
otu_abundance = {}
with open('results/vsearch_analysis/otu_table.txt', 'r') as f:
    f.readline()  # Skip header
    for line in f:
        parts = line.strip().split('\t')
        otu_id = parts[0]
        counts = [int(x) for x in parts[1:]]
        total_count = sum(counts)
        otu_abundance[otu_id] = total_count
        total_reads_all += total_count

# Count assigned reads
assigned_otus = set()
with open('results/vsearch_analysis/fixed_cluster_taxonomy.txt', 'r') as f:
    f.readline()  # Skip header
    for line in f:
        otu_id = line.strip().split('\t')[0]
        assigned_otus.add(otu_id)
        if otu_id in otu_abundance:
            total_reads_assigned += otu_abundance[otu_id]

print(f'Total reads in all OTUs: {total_reads_all}')
print(f'Total reads in taxonomically assigned OTUs: {total_reads_assigned}')
print(f'Percentage of reads assigned taxonomy: {total_reads_assigned/total_reads_all*100:.1f}%')
print(f'Number of OTUs: {len(otu_abundance)} total, {len(assigned_otus)} assigned')

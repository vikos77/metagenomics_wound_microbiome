# 16S rRNA Metagenomics Analysis Pipeline - Complete SOP

## Prerequisites and System Requirements

**Hardware Requirements:**
- Linux system (Ubuntu recommended)
- Minimum 750GB storage space
- 16GB RAM
- 8+ CPU cores
- Internet connection for database downloads

**Software Requirements:**
```bash
sudo apt update
sudo apt install -y sra-toolkit fastqc trimmomatic vsearch ncbi-blast+ wget unzip python3 python3-pip
```

## Step 1: Project Setup and Directory Structure

```bash
# Create main project directory
mkdir diabetic_wound_microbiome
cd diabetic_wound_microbiome

# Create organized subdirectories
mkdir -p raw_data
mkdir -p results/{fastqc_reports,trimmed_reads,vsearch_analysis,databases}
```

## Step 2: Data Download from NCBI SRA

```bash
# Download project metadata
esearch -db sra -query "PRJNA596613" | efetch -format runinfo > project_runinfo.csv

# Examine data structure
head -5 project_runinfo.csv
wc -l project_runinfo.csv  # Check total samples

# Select representative samples for testing (optional - or download all)
# For testing: download 3 samples with different read counts
cd raw_data

# Download specific samples (replace with your chosen SRA IDs)
fasterq-dump SRR10803282  # low reads (~55K)
fasterq-dump SRR10803271  # medium reads (~200K)  
fasterq-dump SRR10803250  # high reads (~600K)

# Verify downloads
ls -lh
wc -l *.fastq
```

## Step 3: Quality Control Assessment

```bash
cd ..  # Back to project root

# Run FastQC on all samples
fastqc raw_data/*.fastq -o results/fastqc_reports/

# Check basic sequence statistics
for file in raw_data/*.fastq; do
    echo "=== $(basename $file) ==="
    # Check sequence length distribution
    awk 'NR%4==2 {lens[length($0)]++} END {for (l in lens) print l, lens[l]}' $file | sort -n | head -5
    echo "Longest reads:"
    awk 'NR%4==2 {lens[length($0)]++} END {for (l in lens) print l, lens[l]}' $file | sort -n | tail -5
done
```

## Step 4: Quality Filtering and Trimming

conda install -c bioconda trimmomatic

```bash
# Quality trim sequences using Trimmomatic
for sample in SRR10803282 SRR10803271 SRR10803250; do
    echo "Processing $sample..."
    trimmomatic SE raw_data/${sample}.fastq \
        results/trimmed_reads/${sample}_trimmed.fastq \
        LEADING:3 TRAILING:3 SLIDINGWINDOW:4:20 MINLEN:100
done

# Compare file sizes before/after trimming
echo "Original sizes:"
ls -lh raw_data/*.fastq
echo "Trimmed sizes:"
ls -lh results/trimmed_reads/
```

## Step 5: Convert FASTQ to FASTA for VSEARCH

```bash
cd results/vsearch_analysis

# Convert each sample to FASTA with proper sample labeling
vsearch --fastq_filter ../trimmed_reads/SRR10803250_trimmed.fastq \
    --fastaout SRR10803250.fasta \
    --relabel SRR10803250.

vsearch --fastq_filter ../trimmed_reads/SRR10803271_trimmed.fastq \
    --fastaout SRR10803271.fasta \
    --relabel SRR10803271.

vsearch --fastq_filter ../trimmed_reads/SRR10803282_trimmed.fastq \
    --fastaout SRR10803282.fasta \
    --relabel SRR10803282.

# Combine all samples
cat SRR10803250.fasta SRR10803271.fasta SRR10803282.fasta > all_samples_combined.fasta

cd ../..  # Back to project root
```

## Step 6: Sequence Dereplication and OTU Clustering

```bash
cd results/vsearch_analysis

# Dereplicate sequences (remove exact duplicates, keep abundance info)
echo "Total sequences before dereplication:"
grep -c "^>" all_samples_combined.fasta

vsearch --derep_fulllength all_samples_combined.fasta \
    --output dereplicated.fasta \
    --sizeout \
    --minuniquesize 2

echo "Unique sequences after dereplication:"
grep -c "^>" dereplicated.fasta

# Cluster sequences into OTUs at 97% similarity
vsearch --cluster_size dereplicated.fasta \
    --id 0.97 \
    --centroids otus.fasta \
    --uc clusters.uc \
    --sizein --sizeout

echo "Number of OTUs (97% similarity):"
grep -c "^>" otus.fasta

cd ../..
```

## Step 7: Create OTU Abundance Table

```bash
# Create OTU abundance table from cluster results
python3 << 'EOF'
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
EOF

# Check OTU table
echo "OTU table preview:"
head -10 results/vsearch_analysis/otu_table.txt
```

## Step 8: Download and Format Reference Database

```bash
cd results/databases

# Download SILVA database
wget https://www.arb-silva.de/fileadmin/silva_databases/qiime/Silva_132_release.zip
unzip Silva_132_release.zip

# Format SILVA database for BLAST
makeblastdb -in SILVA_132_QIIME_release/rep_set/rep_set_16S_only/97/silva_132_97_16S.fna \
    -dbtype nucl \
    -out silva_16s_db \
    -title "SILVA 16S rRNA database"

# Verify database creation
ls silva_16s_db*

cd ../..
```

## Step 9: Taxonomic Assignment using BLAST

```bash
# Run BLAST against SILVA database
blastn -query results/vsearch_analysis/otus.fasta \
    -db results/databases/silva_16s_db \
    -out results/vsearch_analysis/blast_results.txt \
    -outfmt "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore" \
    -max_target_seqs 1 \
    -perc_identity 80 \
    -num_threads 4

# Check BLAST results
echo "Number of BLAST hits:"
wc -l results/vsearch_analysis/blast_results.txt

echo "Similarity range:"
cut -f3 results/vsearch_analysis/blast_results.txt | sort -n | head -5  # lowest
cut -f3 results/vsearch_analysis/blast_results.txt | sort -n | tail -5  # highest
```

## Step 10: Extract Taxonomy Information (Initial Attempt)

```bash
# This step will reveal the taxonomic assignment challenge
python3 << 'EOF'
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
EOF
```

## Step 11: CRITICAL TROUBLESHOOTING - Fix OTU Mapping Issue

**Problem Identified:** OTU table uses cluster numbers (OTU_0, OTU_1) but taxonomy file uses original sequence names. Additionally, size annotations differ between clustering and BLAST steps.

```bash
# Step 11a: Create cluster-to-sequence mapping
awk '$1=="S" {print "OTU_" $2 "\t" $9}' results/vsearch_analysis/clusters.uc > results/vsearch_analysis/cluster_to_sequence_mapping.txt

# Step 11b: Fix the size annotation mismatch
python3 << 'EOF'
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
EOF
```

## Step 12: Data Quality Assessment

```bash
# Check assignment success rate
python3 << 'EOF'
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
EOF
```

## Step 13: Final Genus-Level Analysis

```bash
# Create final genus-level summary
python3 << 'EOF'
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
EOF
```

## Step 14: Results Interpretation

```bash
# Display final results
echo "=== FINAL WOUND MICROBIOME COMPOSITION ==="
head -20 results/vsearch_analysis/corrected_genus_summary.txt

# Compare with original paper findings
echo ""
echo "=== COMPARISON WITH PAPER'S CORE MICROBIOME ==="
echo "Paper's core microbiome: Alcaligenes, Pseudomonas, Burkholderia, Corynebacterium"
echo ""
grep -E "(Alcaligenes|Pseudomonas|Burkholderia|Corynebacterium|Acinetobacter)" results/vsearch_analysis/corrected_genus_summary.txt
```

## Critical Troubleshooting Notes

### Issue 1: Low Taxonomic Assignment Rate
**Symptoms:** <1% of reads assigned taxonomy, abundant OTUs missing assignments
**Cause:** OTU naming mismatch between clustering and BLAST steps
**Solution:** Create base-name mapping ignoring size annotations (Step 11)

### Issue 2: Size Annotation Inconsistencies
**Symptoms:** Same sequence with different `;size=` values in different files
**Cause:** VSEARCH updates size annotations during clustering
**Solution:** Use base sequence names without size annotations for mapping

### Issue 3: Database Format Issues
**Symptoms:** BLAST database errors
**Cause:** SILVA database not in BLAST format
**Solution:** Use `makeblastdb` to format SILVA FASTA files

## Expected Results

**Final Output Should Show:**
- 85-90% of reads receiving taxonomic assignments
- Core wound pathogens: Pseudomonas, Acinetobacter, Burkholderia, Alcaligenes
- Individual sample variation in microbiome composition
- 150+ bacterial genera detected across samples

## File Structure After Completion

```
diabetic_wound_microbiome/
├── raw_data/
│   └── *.fastq
├── results/
│   ├── fastqc_reports/
│   ├── trimmed_reads/
│   ├── databases/
│   └── vsearch_analysis/
│       ├── otu_table.txt
│       ├── fixed_cluster_taxonomy.txt
│       └── corrected_genus_summary.txt
└── project_runinfo.csv
```

## Pipeline Validation

Your analysis is successful if:
1. Taxonomic assignment rate >80%
2. Core wound pathogens detected in top genera
3. Individual sample variation observed
4. Total reads processed matches input data
5. Genus-level results biologically meaningful

## Computational Requirements

- **Time:** 2-4 hours for 3 samples
- **Storage:** ~2GB for databases, ~1GB for analysis files  
- **Memory:** 8GB RAM sufficient for most steps
- **CPU:** BLAST benefits from multiple cores (use `-num_threads`)

## Next Steps

After completing this pipeline:
1. Compare results with QIIME2 analysis
2. Create visualizations of microbiome composition
3. Perform statistical analysis of sample differences
4. Scale up to analyze all 122 samples from the study

# QIIME2 16S rRNA Metagenomics Analysis Pipeline - Complete SOP

## Prerequisites and System Requirements

**Hardware Requirements:**
- Linux system (Ubuntu recommended)
- Minimum 750GB storage space
- 16GB RAM minimum (32GB recommended for larger datasets)
- 8+ CPU cores
- Internet connection for database downloads

**Software Requirements:**
- Conda/Miniconda installed
- Python 3.8+ environment support
- Basic command line familiarity

## Step 1: QIIME2 Installation

### Method 1: Direct Conda/Mamba Installation (Recommended)
```bash
# Install QIIME2 using mamba (most reliable method)
wget https://data.qiime2.org/distro/amplicon/qiime2-amplicon-2024.10-py310-linux-conda.yml
mamba env create -n qiime2-2024.10 --file qiime2-amplicon-2024.10-py310-linux-conda.yml


# Activate QIIME2 environment
conda activate qiime2-2024.10

# Test installation
qiime --help
qiime info
```

### Method 2: YAML File Installation (Alternative)
```bash
# Download YAML file (may have SSL certificate issues)
wget https://data.qiime2.org/distro/core/qiime2-2023.5-py38-linux-conda.yml
conda env create -n qiime2-2023.5 --file qiime2-2023.5-py38-linux-conda.yml
```

**Troubleshooting Installation Issues:**
- **Certificate errors**: Use Method 1 (direct conda installation)
- **Environment conflicts**: Create a fresh conda environment
- **Permission issues**: Ensure conda has write permissions to installation directory

## Step 2: Project Setup and Data Preparation

```bash
# Ensure you're in your main project directory
cd /path/to/your/project  # e.g., metegenomics_wound_microbiome

# Activate QIIME2 environment (must be done in every new terminal session)
conda activate qiime2-2023.5

# Create QIIME2 analysis directory
mkdir -p results/qiime2_analysis
cd results/qiime2_analysis

# Verify you have trimmed FASTQ files from previous analysis
ls ../trimmed_reads/
```

## Step 3: Create Sample Manifest File

QIIME2 requires a manifest file to import single-end sequencing data:

```bash
# Create manifest file for sample import
cat > manifest.tsv << EOF
sample-id	absolute-filepath	direction
SRR10803250	$(pwd)/../trimmed_reads/SRR10803250_trimmed.fastq	forward
SRR10803271	$(pwd)/../trimmed_reads/SRR10803271_trimmed.fastq	forward
SRR10803282	$(pwd)/../trimmed_reads/SRR10803282_trimmed.fastq	forward
EOF

# Verify manifest file paths are correct
cat manifest.tsv

# Test that files exist
for file in $(cut -f2 manifest.tsv | tail -n +2); do
    echo "Checking: $file"
    ls -lh "$file"
done
```

**Critical Path Issues:**
- Ensure absolute paths (starting with `/`) in manifest file
- Verify all files exist and are readable
- Check for correct tab-separated format (not spaces)

## Step 4: Import Sequences into QIIME2

```bash
# Import sequences from manifest
qiime tools import \
    --type 'SampleData[SequencesWithQuality]' \
    --input-path manifest.tsv \
    --output-path sequences.qza \
    --input-format SingleEndFastqManifestPhred33V2

# Verify import success
qiime tools peek sequences.qza
ls -lh sequences.qza
```

**Expected Output:**
- `sequences.qza` file created (typically 50-100MB for our dataset)
- UUID and data format information displayed by `peek` command

## Step 5: Sequence Quality Assessment

```bash
# Create sequence summary visualization
qiime demux summarize \
    --i-data sequences.qza \
    --o-visualization sequences_summary.qzv

# Export visualization for examination (since GUI viewing may not be available)
qiime tools export \
    --input-path sequences_summary.qzv \
    --output-path sequences_summary_exported

# Check exported files
ls sequences_summary_exported/
```

The `.qzv` files contain interactive HTML reports. If you have GUI access, you can view them with:
```bash
qiime tools view sequences_summary.qzv
```

```bash
iime demux summarize \
  --i-data sequences.qza \
  --o-visualization sequences.qzv
```

## Step 6: Sequence Denoising with DADA2

DADA2 in QIIME2 performs error correction and identifies Amplicon Sequence Variants (ASVs):

```bash
# Denoise sequences using DADA2
qiime dada2 denoise-single \
    --i-demultiplexed-seqs sequences.qza \
    --p-trim-left 0 \
    --p-trunc-len 200 \
    --o-table feature_table.qza \
    --o-representative-sequences rep_seqs.qza \
    --o-denoising-stats denoising_stats.qza

# Verify outputs
ls -lh *.qza
```

**Parameter Explanations:**
- `--p-trim-left 0`: No additional left trimming (already done in preprocessing)
- `--p-trunc-len 200`: Truncate sequences at 200bp (conservative for quality)
- `feature_table.qza`: ASV abundance table (equivalent to OTU table)
- `rep_seqs.qza`: Representative sequences for each ASV
- `denoising_stats.qza`: Quality control statistics

**Parameter Optimization Notes:**
- Increase `--p-trunc-len` to 300-400 if quality scores permit
- Use `--p-trim-left 5-10` if adapter sequences remain
- Monitor denoising stats to balance quality vs. data retention

## Step 7: Examine Denoising Results

```bash
# Create denoising statistics visualization
qiime metadata tabulate \
    --m-input-file denoising_stats.qza \
    --o-visualization denoising_stats.qzv

# Summarize feature table
qiime feature-table summarize \
    --i-table feature_table.qza \
    --o-visualization feature_table_summary.qzv

# Export feature table for examination
qiime tools export \
    --input-path feature_table.qza \
    --output-path exported_feature_table

# Convert BIOM format to readable TSV
biom convert \
    -i exported_feature_table/feature-table.biom \
    -o exported_feature_table/feature-table.tsv \
    --to-tsv

# Examine results
biom summarize-table -i exported_feature_table/feature-table.biom
head -10 exported_feature_table/feature-table.tsv
```

## Step 8: Taxonomic Classification - Initial Attempt (Pre-trained Classifier)

**WARNING**: This step commonly fails due to version incompatibilities.

```bash
# Attempt to download pre-trained SILVA classifier
wget -O silva-138-99-515-806-nb-classifier.qza \
    "https://data.qiime2.org/2023.5/common/silva-138-99-515-806-nb-classifier.qza"

# Attempt taxonomic classification
qiime feature-classifier classify-sklearn \
    --i-classifier silva-138-99-515-806-nb-classifier.qza \
    --i-reads rep_seqs.qza \
    --o-classification taxonomy.qza
```

**Common Error:**
```
ValueError: The scikit-learn version (0.24.1) used to generate this artifact does not match the current version of scikit-learn installed (1.4.2). Please retrain your classifier for your current deployment to prevent data-corruption errors.
```

**This error occurs because:**
- Pre-trained classifiers are built with specific scikit-learn versions
- QIIME2 updates often include newer scikit-learn versions
- Classifier compatibility is strictly enforced

## Step 9: CRITICAL TROUBLESHOOTING - Alternative Taxonomic Classification

When pre-trained classifiers fail, use BLAST-based classification:

### Step 9a: Convert SILVA Database to QIIME2 Format

```bash
# Navigate to databases directory (from previous VSEARCH analysis)
cd ../databases

# Check if SILVA database exists from VSEARCH analysis
ls SILVA_132_QIIME_release/

# Import SILVA reference sequences into QIIME2 format
qiime tools import \
    --type 'FeatureData[Sequence]' \
    --input-path SILVA_132_QIIME_release/rep_set/rep_set_16S_only/97/silva_132_97_16S.fna \
    --output-path silva_seqs.qza

# Import SILVA taxonomy into QIIME2 format
qiime tools import \
    --type 'FeatureData[Taxonomy]' \
    --input-path SILVA_132_QIIME_release/taxonomy/16S_only/97/taxonomy_7_levels.txt \
    --input-format HeaderlessTSVTaxonomyFormat \
    --output-path silva_taxonomy.qza

# Verify imports
qiime tools peek silva_seqs.qza
qiime tools peek silva_taxonomy.qza

# Return to QIIME2 analysis directory
cd ../qiime2_analysis
```

**Troubleshooting Database Import:**
- Ensure SILVA files exist from previous VSEARCH analysis
- Verify file paths are correct
- Check that taxonomy file is in proper TSV format
- Re-download SILVA if necessary

### Step 9b: BLAST-based Taxonomic Classification

```bash
# Perform BLAST-based taxonomic classification
qiime feature-classifier classify-consensus-blast \
    --i-query rep_seqs.qza \
    --i-reference-reads ../databases/silva_seqs.qza \
    --i-reference-taxonomy ../databases/silva_taxonomy.qza \
    --o-classification taxonomy.qza \
    --o-search-results blast_search_results.qza \
    --p-perc-identity 0.8 \
    --p-num-threads 4

# Verify classification completed
ls -lh taxonomy.qza blast_search_results.qza
```

**Parameter Explanations:**
- `--p-perc-identity 0.8`: 80% minimum sequence identity for assignment
- `--p-num-threads 4`: Use 4 CPU cores for parallel processing
- `blast_search_results.qza`: Detailed BLAST search results for reference

# During this step the qiime feature-classifier might not work if there are any R packages missing, which
# was the case here and then the missing package was installed manually by starting R

#Start a  R session
R

# Install BiocManager if not present
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install the missing package
BiocManager::install("GenomeInfoDbData")
quit()


## Step 10: Examine Taxonomic Results

```bash
# Create taxonomy visualization
qiime metadata tabulate \
    --m-input-file taxonomy.qza \
    --o-visualization taxonomy.qzv

# Export taxonomy for examination
qiime tools export \
    --input-path taxonomy.qza \
    --output-path exported_taxonomy

# Examine taxonomic assignments
head -10 exported_taxonomy/taxonomy.tsv
wc -l exported_taxonomy/taxonomy.tsv

# Check assignment success rate
echo "Total ASVs: $(grep -c '^>' exported_feature_table/feature-table.tsv)"
echo "Assigned ASVs: $(tail -n +2 exported_taxonomy/taxonomy.tsv | wc -l)"
```

## Step 11: Create Taxonomic Visualizations

```bash
# Create taxa bar plots for visualization
qiime taxa barplot \
    --i-table feature_table.qza \
    --i-taxonomy taxonomy.qza \
    --o-visualization taxa_barplot.qzv

# Collapse feature table to genus level
qiime taxa collapse \
    --i-table feature_table.qza \
    --i-taxonomy taxonomy.qza \
    --p-level 6 \
    --o-collapsed-table genus_table.qza

# Export genus-level table
qiime tools export \
    --input-path genus_table.qza \
    --output-path exported_genus_table

# Convert genus table to readable format
biom convert \
    -i exported_genus_table/feature-table.biom \
    -o exported_genus_table/genus_table.tsv \
    --to-tsv

# Examine genus-level results
head -15 exported_genus_table/genus_table.tsv
```

## Step 12: Process Results for Analysis

The genus-level table contains full taxonomic strings that need processing:

```bash
# Create clean genus-level summary
python3 << 'EOF'
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
EOF

# Display results
echo "=== TOP 20 GENERA FROM QIIME2/DADA2 ANALYSIS ==="
head -21 qiime2_genus_summary.txt
```

## Step 13: Results Validation and Comparison

```bash
# Compare with core wound microbiome expectations
echo "=== CORE WOUND MICROBIOME VALIDATION ==="
echo "Expected genera: Acinetobacter, Pseudomonas, Burkholderia, Alcaligenes, Achromobacter"
echo ""

for genus in "Acinetobacter" "Pseudomonas" "Burkholderia" "Alcaligenes" "Achromobacter"; do
    echo "--- $genus ---"
    grep -i "$genus" qiime2_genus_summary.txt | head -1
done
```

## Critical Troubleshooting Guide

### Issue 1: Pre-trained Classifier Version Mismatch
**Symptoms:**
```
ValueError: The scikit-learn version (0.24.1) used to generate this artifact does not match the current version of scikit-learn installed (1.4.2)
```

**Solutions:**
1. Use BLAST-based classification instead of sklearn classifier
2. Train your own classifier (time-intensive)
3. Use older QIIME2 version matching the classifier

**Prevention:**
- Always check classifier compatibility with your QIIME2 version
- Use BLAST-based methods for more reliable results

### Issue 2: Database Import Failures
**Symptoms:**
- Import commands fail with format errors
- Taxonomy files not recognized

**Solutions:**
```bash
# Verify file formats before import
head -5 SILVA_132_QIIME_release/taxonomy/16S_only/97/taxonomy_7_levels.txt

# Use correct import format
qiime tools import \
    --type 'FeatureData[Taxonomy]' \
    --input-path taxonomy_file.txt \
    --input-format HeaderlessTSVTaxonomyFormat \
    --output-path taxonomy.qza
```

### Issue 3: Manifest File Path Errors
**Symptoms:**
- Import fails with "file not found" errors
- Path resolution issues

**Solutions:**
```bash
# Use absolute paths in manifest
cat > manifest.tsv << EOF
sample-id	absolute-filepath	direction
SRR10803250	$(pwd)/../trimmed_reads/SRR10803250_trimmed.fastq	forward
EOF

# Test all paths before import
for file in $(cut -f2 manifest.tsv | tail -n +2); do ls -lh "$file"; done
```

### Issue 4: DADA2 Parameter Optimization
**Symptoms:**
- Very low read retention after denoising
- Poor ASV quality

**Solutions:**
```bash
# Adjust parameters based on quality profiles
qiime dada2 denoise-single \
    --p-trim-left 5 \           # Remove low-quality start bases
    --p-trunc-len 300 \         # Increase length if quality permits
    --p-max-ee 2.0 \           # Adjust error threshold
```

### Issue 5: Memory/Performance Issues
**Symptoms:**
- Process killed during analysis
- Extremely slow processing

**Solutions:**
```bash
# Increase available threads
--p-num-threads 8

# For large datasets, consider subsampling
qiime feature-table filter-samples \
    --i-table feature_table.qza \
    --p-min-frequency 1000 \
    --o-filtered-table filtered_table.qza
```

## Expected Results and Validation

### Success Criteria:
1. **DADA2 Processing**: >60% read retention after denoising
2. **ASV Detection**: 500-1000 ASVs typical for wound samples
3. **Taxonomic Assignment**: >80% of reads assigned to genus level
4. **Biological Relevance**: Core wound pathogens detected

### Typical Output:
- **Total reads processed**: 300K-500K
- **ASVs identified**: 500-1000
- **Genera detected**: 100-200
- **Core pathogens**: Acinetobacter, Pseudomonas, Burkholderia present

### Quality Checks:
```bash
# Check key metrics
echo "=== ANALYSIS QUALITY METRICS ==="
echo "Total samples: $(grep -c 'SRR' manifest.tsv)"
echo "ASVs detected: $(tail -n +3 exported_feature_table/feature-table.tsv | wc -l)"
echo "Genera identified: $(tail -n +2 qiime2_genus_summary.txt | wc -l)"
echo "Top genus abundance: $(tail -n +2 qiime2_genus_summary.txt | head -1 | cut -f5)%"
```

## File Structure After Completion

```
results/qiime2_analysis/
├── manifest.tsv                        # Sample manifest
├── sequences.qza                       # Imported sequences
├── sequences_summary.qzv               # Quality summary
├── feature_table.qza                   # ASV abundance table
├── rep_seqs.qza                       # Representative sequences
├── denoising_stats.qza                # DADA2 statistics
├── taxonomy.qza                       # Taxonomic assignments
├── blast_search_results.qza           # BLAST results
├── genus_table.qza                    # Genus-level table
├── taxa_barplot.qzv                   # Visualization
├── exported_feature_table/            # Exported data
│   ├── feature-table.biom
│   └── feature-table.tsv
├── exported_taxonomy/                 # Exported taxonomy
│   └── taxonomy.tsv
├── exported_genus_table/              # Genus-level data
│   ├── feature-table.biom
│   └── genus_table.tsv
└── qiime2_genus_summary.txt           # Final results
```

## Performance Benchmarks

**Typical Analysis Time:**
- Data import: 5-10 minutes
- DADA2 denoising: 10-30 minutes
- BLAST classification: 15-45 minutes
- Total pipeline: 1-2 hours

**Resource Usage:**
- Memory: 4-16GB RAM during DADA2
- Storage: 1-2GB for intermediate files
- CPU: Benefits from 4-8 cores

## Integration with VSEARCH Results

To compare QIIME2 results with VSEARCH analysis:

```bash
# Create comparison summary
echo "=== METHOD COMPARISON ==="
echo "VSEARCH OTUs: $(grep -c '^OTU_' ../vsearch_analysis/otu_table.txt)"
echo "QIIME2 ASVs: $(tail -n +3 exported_feature_table/feature-table.tsv | wc -l)"
echo ""
echo "VSEARCH Genera: $(tail -n +2 ../vsearch_analysis/corrected_genus_summary.txt | wc -l)"
echo "QIIME2 Genera: $(tail -n +2 qiime2_genus_summary.txt | wc -l)"

# Compare top genera
echo ""
echo "Top 5 genera comparison:"
echo "VSEARCH:"
head -6 ../vsearch_analysis/corrected_genus_summary.txt
echo ""
echo "QIIME2:"
head -6 qiime2_genus_summary.txt
```

## Next Steps

After completing this pipeline:
1. Create visualizations comparing both methods
2. Perform statistical analysis of genus abundance differences
3. Analyze sample-specific microbiome patterns  
4. Scale analysis to full 122-sample dataset
5. Generate publication-ready figures

## Key Advantages of QIIME2 Approach

1. **Standardization**: Reproducible workflows with provenance tracking
2. **ASV Resolution**: More precise than 97% similarity OTUs
3. **Integration**: Built-in visualizations and statistical tools
4. **Community**: Large user base and extensive documentation
5. **Quality Control**: Comprehensive QC metrics and visualizations

This pipeline provides a robust, standardized approach to 16S rRNA analysis that complements the transparent, customizable VSEARCH workflow.

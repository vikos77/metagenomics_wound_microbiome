# Create comparative visualization script
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set style for publication-quality figures
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams.update({'font.size': 12, 'figure.dpi': 300})

# Read VSEARCH results
vsearch_data = []
with open('vsearch_genus_summary.txt', 'r') as f:
    header = f.readline().strip().split('\t')
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 6:
            genus = parts[0]
            total = int(parts[4])
            percent = float(parts[5])
            vsearch_data.append([genus, total, percent, 'VSEARCH'])

# Read QIIME2 results
qiime2_data = []
with open('qiime2_genus_summary.txt', 'r') as f:
    header = f.readline().strip().split('\t')
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 5:
            genus = parts[0]
            total = int(parts[4])
            percent = float(parts[5])
            qiime2_data.append([genus, total, percent, 'QIIME2'])

# Combine data
all_data = vsearch_data + qiime2_data
df = pd.DataFrame(all_data, columns=['Genus', 'Total_Reads', 'Percent', 'Method'])

print(f"VSEARCH: {len(vsearch_data)} genera")
print(f"QIIME2: {len(qiime2_data)} genera")

# Create figure with multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Microbiome Analysis Comparison: VSEARCH vs QIIME2/DADA2', fontsize=16, fontweight='bold')

# Plot 1: Top 10 genera comparison
core_genera = ['Acinetobacter', 'Pseudomonas', 'Burkholderia-Caballeronia-Paraburkholderia', 
               'Achromobacter', 'Alcaligenes', 'Stenotrophomonas', 'Escherichia-Shigella']

comparison_data = []
for genus in core_genera:
    vsearch_percent = next((item[2] for item in vsearch_data if item[0] == genus), 0)
    qiime2_percent = next((item[2] for item in qiime2_data if item[0] == genus), 0)
    comparison_data.append([genus, vsearch_percent, qiime2_percent])

comp_df = pd.DataFrame(comparison_data, columns=['Genus', 'VSEARCH', 'QIIME2'])
x = np.arange(len(core_genera))
width = 0.35

axes[0,0].bar(x - width/2, comp_df['VSEARCH'], width, label='VSEARCH', alpha=0.8)
axes[0,0].bar(x + width/2, comp_df['QIIME2'], width, label='QIIME2', alpha=0.8)
axes[0,0].set_xlabel('Genus')
axes[0,0].set_ylabel('Relative Abundance (%)')
axes[0,0].set_title('Core Wound Microbiome Comparison')
axes[0,0].set_xticks(x)
axes[0,0].set_xticklabels([g.replace('-', '-\n') for g in core_genera], rotation=45, ha='right')
axes[0,0].legend()
axes[0,0].grid(True, alpha=0.3)

print("Plot 1 completed: Core genera comparison")

plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust layout for title
plt.show()  # Show the plots
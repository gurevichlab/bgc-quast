# About
BGC-QUAST: quality assessment tool for genome mining software

## Requirements
* Python 3
* pyyaml

## Installation
Not needed

## Running
BGC-QUAST supports three working modes intended for different groups of users and requiring different sets of input files.

### 1. Reference vs assembly-based genome mining evaluation
**Use case**: The same genome mining method was applied to a high-quality reference genome and draft assemblies of the same organism. 

**BGC-QUAST reports**: **BGC-QUAST applicability**: Our tool assesses how well the genome mining method performs on real-life sequence

**Applicability**: Users might see how different sequencing technologies (e.g., short-read vs long-read) or computational processing steps (e.g., different assembly methods or software parameters) affect
 
### 2. Genome mining tools comparison 

### 3. Multiple genomes summary creation  


Sample analysis of the antiSMASH genome mining results
```commandline
./bgc-quast.py test_data/antiSMASH_out/sample_genome.json
```

Reading the BGC-QUAST report 
```commandline
less bgc_quast_results/report.txt
```
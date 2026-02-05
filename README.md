# BGC-QUAST Manual

1. [About BGC-QUAST](#sec_about) </br>
1.1. [Requirements](#sec_req) </br>
1.2. [Installation](#sec_install) </br>
1.3. [Supported genome mining tools](#sec_tools) </br>
1.4. [Command-line Options](#sec_cmd_options) </br>
2. [Running modes](#sec_run_modes)</br> 
2.1. [Compare-to-reference mode](#sec_run_mode_1) </br>
2.2. [Compare-tools mode](#sec_run_mode_2) </br>
2.3. [Compare-samples mode](#sec_run_mode_3) </br>
3. [Feedback and bug reports](#sec_feedback)</br>


<a name="sec_about"></a>
# About BGC-QUAST

**BGC-QUAST** is a quality assessment tool for genome mining software — 
tools used for predicting biosynthetic gene clusters (BGCs). 
It provides summary statistics, comparative analyses, and interactive visualization 
of BGC prediction results from multiple tools and datasets.

BGC-QUAST is distributed under the MIT License.
See the [LICENSE](LICENSE) file for details.

<a name="sec_req"></a>
## Requirements

- Python ≥ 3.9 (tested with Python 3.9–3.13)
- A conda-compatible environment manager: 
[Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) or 
[Mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)

All required Python dependencies are specified in the
[`environment.yml`](environment.yml) file.

<a name="sec_install"></a>
## Installation

### 1. Get the source code

Clone the repository:  

```bash
git clone https://github.com/gurevichlab/bgc-quast.git
cd bgc-quast
```  
Alternatively, download the repository as a ZIP file from [GitHub](https://github.com/gurevichlab/bgc-quast) and extract it.

### 2. Create and activate the conda environment

```bash
conda env create -f environment.yml
conda activate bgc-quast
```

### 3. Verify installation

```bash
python bgc-quast.py --help
```

<a name="sec_tools"></a>
## Supported genome mining tools
Currently supported genome mining tools and their output formats:  
- antiSMASH: `.json`  
- GECCO: `.tsv`  
- deepBGC: `.json`, `.tsv`  

Compressed files (`.gz`) are supported. See [test_data](test_data) for example files. 

<a name="sec_cmd_options"></a>
## Command-line Options
```bash
usage: bgc-quast.py [-h] [--output-dir DIR] [--threads INT] [--mode {auto,compare-to-reference,compare-tools,compare-samples}]
                    [--min-bgc-length INT] [--names NAME1,NAME2 ...] [--genome FILE ...] [--debug]
                    [mode-specific options] <GENOME_MINING_RESULT>
```
### Positional Arguments

- `GENOME_MINING_RESULT`: Paths to genome mining outputs (antiSMASH `.json`, GECCO `.tsv`, or deepBGC `.json`/`.tsv`)

---

### Basic options

| Option                        | Description                                                                                                           |
|-------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `-h, --help`                  | Show help message and exit                                                                                            |
| `--output-dir DIR, -o DIR`   | Output directory [default: ./bgc-quast-results/<date_time>]                                                                        |
| `--threads INT, -t INT`      | Number of threads [default: 1]                                                                                        |
| `--debug`                    | Keep intermediate files                                                                                               |
| `--genome, -g [FILE ...]`     | Path to the genome FASTA/GenBank file; can accept multiple paths; required for `--min-bgc-length` and `edge-distance` |
| `--names NAME1,NAME2 ...` | Custom names for the input genome mining results in reports                                                           |
| `--min-bgc-length INT` | Minimum BGC length in bp.  [default: 0]                                                                               |
| `--edge-distance INT` | Margin (in bp) from contig edges used to classify BGC completeness                                                    |
| `--mode {auto,compare-to-reference,compare-tools,compare-samples}` | [Running mode](#sec_run_modes) that controls how BGC-QUAST interprets the inputs                                                   |

### Compare-to-reference options

| Option                                     | Description                                                   |
|--------------------------------------------|---------------------------------------------------------------|
| `--quast-output-dir DIR, -q DIR`          | QUAST output (required for the compare-to-reference mode)     |
| `--reference-mining-result FILE, -r FILE` | genome mining result on the reference genome                  |
| `--reference-genome FILE`                | Reference genome input (FASTA/GenBank)                        |
| `--ref-name REF_NAME`                    | Custom name for the reference genome mining result in reports |

### Compare-tools options
| Option                                     | Description                                           |
|--------------------------------------------|-------------------------------------------------------|
| `--overlap-threshold FLOAT`          | BGC overlap threshold percentage in (0,1] for COMPARE-TOOLS mode [default: 0.9]      | 


<a name="sec_run_modes"></a>
## Running modes

BGC-QUAST supports **three running modes**, each designed for a different analysis scenario.
Each mode computes the basic BGC quality metrics listed below and may additionally produce further metrics and outputs specific to the selected mode. The `example_outputs/` directory contains precomputed BGC-QUAST reports generated on the provided test data in all three modes.

### Basic metrics
The following BGC prediction quality metrics are computed in **all running modes**:  
- **Counts**  
  Total number of detected BGCs and counts per BGC product type.  
- **Completeness**  
  Number of complete BGCs versus fragmented BGCs (located on contig edges), reported overall and per product type.  
- **Length statistics**  
  Mean BGC length, reported overall and stratified by product type and completeness.  
- **Gene count statistics**  
  Mean number of genes per BGC, reported overall and stratified by product type and completeness.  

<a name="sec_run_mode_1"></a>
### 1. Compare-to-reference mode

**Use case**  
Assess how well BGCs predicted on draft assemblies match the predictions obtained from a high-quality reference genome. 

> **Note**  
> The same genome mining tool (e.g., antiSMASH) must be used for both the assemblies and the reference genome.  
> Draft assemblies must be aligned against the reference using
[QUAST](https://quast.sourceforge.net/), and the corresponding QUAST output directory must be provided to BGC-QUAST.

**Command (general form)**  

```bash
python bgc-quast.py <assembly1_genome_mining_results> \
                    <assembly2_genome_mining_results> \
                    ... \
  --mode compare-to-reference \
  --reference-mining-result <reference_genome_mining_results> \
  --quast-output-dir <quast_output_dir> \
  --output-dir <output_dir>
```  

**Example (test data)**  

```bash
python bgc-quast.py \
  test_data/assembly_10_mining/antiSMASH/assembly_10.json.gz \
  test_data/assembly_20_mining/antiSMASH/assembly_20.json.gz \
  -r test_data/reference_mining/antiSMASH/reference.json.gz \
  -q test_data/quast_out/
```
The BGC-QUAST reports will be saved in `./bgc-quast-results/latest/`.
See the example output in 
[`example_outputs/compare-to-reference/`](example_outputs/compare-to-reference/).

**Mode-specific quality metrics**  
- Number of **fully recovered**, **partially recovered**, and **missed** BGCs in the assemblies, with respect to BGCs predicted in the reference genome (considered as ground truth). Reported overall and stratified by product type and completeness.

<a name="sec_run_mode_2"></a>
### 2. Compare-tools mode

**Use case**  
Compare BGCs predicted by different genome mining tools applied to the same genome sequence.

> **Note**
> All genome mining tools must be run on the **same input genome sequence**. If this is unclear from the input file names (e.g., deepBGC does not include the input genome name in its output), the running mode should be explicitly specified using `--mode compare-tools`.    
 
**Command (general form)**  

```bash
python bgc-quast.py <tool1_genome_mining_results> \
                    <tool2_genome_mining_results> \
                    ... \
  --mode compare-tools \
  --overlap-threshold <fraction> \
  --output-dir <output_dir>
```

**Example (test data)**  

```bash
python bgc-quast.py \
  test_data/assembly_10_mining/antiSMASH/assembly_10.json.gz \
  test_data/assembly_10_mining/deepBGC/deepBGC.bgc.tsv \
  test_data/assembly_10_mining/GECCO/assembly_10.clusters.tsv \
  --mode compare-tools  
```
The BGC-QUAST reports will be saved in `./bgc-quast-results/latest/`.
See the example output in 
[`example_outputs/compare-tools/`](example_outputs/compare-tools/).

**Mode-specific quality metrics**  
- Number of tool-specific (**unique**) and **shared** BGCs across genome mining tools, reported overall and stratified by product type and completeness.  
- **Venn diagrams** illustrating overlaps between BGC predictions produced by different tools.

<a name="sec_run_mode_3"></a>
### 3. Compare-samples mode

**Use case**  
Summarize and compare BGC predictions produced by a single genome mining tool across multiple genomes or metagenomic samples. This mode is intended for cohort-level analysis rather than direct BGC-to-BGC comparison.

> **Note**  
> All input genome mining results must be produced by the **same genome mining tool**.  
> When sample names are not explicitly provided (`--names`), they are inferred from input file names.

**Command (general form)**


```bash
python bgc-quast.py <sample1_genome_mining_results> \
                    <sample2_genome_mining_results> \
                    ... \
  --mode compare-samples \
  --names <sample1>,<sample2>,... \
  --genome <sample1_genome> <sample2_genome> ... \
  --output-dir <output_dir>
```

**Example (test data)**  

```bash
python bgc-quast.py \
  test_data/assembly_10_mining/antiSMASH/assembly_10.json.gz \
  test_data/assembly_20_mining/antiSMASH/assembly_20.json.gz 
```
The BGC-QUAST reports will be saved in `./bgc-quast-results/latest/`.
See the example output in 
[`example_outputs/compare-samples/`](example_outputs/compare-samples/).

**Mode-specific quality metrics**  
- This mode currently reports only the **basic BGC quality metrics described above**, aggregated and summarized across samples.

<a name="sec_feedback"></a>
## Feedback and bug reports
You can leave your comments and bug reports at [https://github.com/gurevichlab/bgc-quast/issues](https://github.com/gurevichlab/bgc-quast/issues) (*recommended way*) 
or sent it via e-mail to [alexey.gurevich@helmholtz-hips.de](alexey.gurevich@helmholtz-hips.de).

Your comments, bug reports, and suggestions are **very welcome**.
They will help us to improve BGC-QUAST further.

If you have any trouble running BGC-QUAST, please attach `bgc-quast.log` from the output directory.

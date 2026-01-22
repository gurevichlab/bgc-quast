# BGC-QUAST Manual

1. [About BGC-QUAST](#sec_about) </br>
2. [Running Modes](#sec_run_modes)</br> 
3. [Feedback and bug reports](#sec_feedback)</br>

<a name="sec_about"></a>
# About BGC-QUAST

**BGC-QUAST** is a quality assessment tool for genome mining (GM) software — 
tools used for the prediction of biosynthetic gene clusters (BGCs). 
It provides summary statistics, comparative analyses, and interactive visualization 
of BGC prediction results from multiple tools and datasets.

---

## Requirements

- Python 3
- `pyyaml`, `pandas`, `matplotlib` and `matplotlib-venn` Python packages

---

## Installation

No installation needed — just clone the repository and run the script.

---

## Supported Genome Mining Tools
Currently supported genome mining tools and their output formats:
- antiSMASH: `.json`
- GECCO: `.tsv`
- deepBGC: `.json`, `.tsv`

Compressed files (`.gz`) are supported. See [test_data](test_data) for example files. 

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

| Option                        | Description                                               |
|-------------------------------|-----------------------------------------------------------|
| `-h, --help`                  | Show help message and exit                                |
| `--output-dir DIR, -o DIR`   | Output directory [default: timestamped folder]            |
| `--threads INT, -t INT`      | Number of threads [default: 1]                            |
| `--debug`                    | Keep intermediate files                                   |
| `--genome, -g [FILE ...]`     | Path to the genome FASTA/GenBank file; can accept multiple paths; required for `--min-bgc-length` and `edge-distance` |
| `--names NAME1,NAME2 ...` | Custom names for the input genome mining results in reports |
| `--min-bgc-length INT` |  Minimum BGC length in bp.  [default: 0] |
| `--edge-distance INT` | Margin (in bp) from contig edges used to classify BGC completeness |
| `--mode {auto,compare-to-reference,compare-tools,compare-samples}` | Running mode that controls how BGC-QUAST interprets the inputs |

---

### Compare-to-reference options

| Option                                     | Description                                           |
|--------------------------------------------|-------------------------------------------------------|
| `--quast-output-dir DIR, -q DIR`          | QUAST output (required for reference-based mode)      |
| `--reference-mining-result FILE, -r FILE` | GM result on the reference genome                     |
| `--reference-genome FILE`                | Reference genome input (FASTA/GenBank)                |
| `--ref-name REF_NAME`                    | Custom name for the reference genome mining result in reports |

---

### Compare-tools options
| Option                                     | Description                                           |
|--------------------------------------------|-------------------------------------------------------|
| `--overlap-threshold FLOAT`          | BGC overlap threshold percentage in (0,1] for COMPARE-TOOLS mode [default: 0.9]      | 


---
<a name="sec_run_modes"></a>
## Running Modes

BGC-QUAST supports three running modes depending on your use case. Each mode has its own expected inputs and output structure.
However, basic BGC quality metrics are computed in either of them.

### Basic quality metrics
- BGC count: total, per product type
- Completeness: number of complete vs. fragmented BGCs, per type
- Length statistics: mean, median, N50 of BGC lengths (overall and per type/completeness)
- Gene content: average and median number of genes per BGC (overall and per type/completeness)

### 1. Compare-to-Reference

**Use case**: Assess how well BGCs predicted on draft assemblies match the predictions from a high-quality reference genome.

**Command example**:
```bash
./bgc-quast.py assembly_run1.json assembly_run2.json \
  --reference-mining-result reference_run.json \
  --quast-output-dir quast_output \
  --reference-genome Reference_name \
  --output-dir results/compare_to_reference

```

**Output:**
- Matching metrics (e.g., full/partial/missed BGCs)
- Side-by-side interactive browser comparing BGCs across assemblies and reference

### 2. Compare-Tools
***Use case***: Compare different GM tools run on the same genome sequence.

**Command example**:

```bash
./bgc-quast.py antiSMASH_run.json GECCO_run.tsv deepBGC_run.json \
  --overlap-threshold 0.5 \
  --genome antiSMASH_run.fasta,GECCO_run.fasta,deepBGC_run.fasta \
  --min-bgc-length 10000 \
  --output-dir results/compare_tools
```

**Output**:
- Tool overlap plots (Venn diagrams)
- Interactive browser showing tool-specific and shared BGCs

### 3. Compare-Samples

**Use case**: Summarize BGC predictions from a single GM tool across multiple genomes or metagenomic samples.

**Command example**:

```bash
./bgc-quast.py sample1.json sample2.json sample3.json \
  --names Sample1,Sample2 \
  --genome sample1.gbk,sample2.gbk,sample3.gbk \
  --edge-distance 500
  --output-dir results/compare_samples
```

**Output**:
- Per-sample summary stats (BGC count, types, lengths)
- One interactive BGC browser per sample
- Aggregate statistics and plots across the cohort


<a name="sec_feedback"></a>
## Feedback and bug reports
You can leave your comments and bug reports at [https://github.com/gurevichlab/bgc-quast/issues](https://github.com/gurevichlab/bgc-quast/issues) (*recommended way*) 
or sent it via e-mail to [alexey.gurevich@helmholtz-hips.de](alexey.gurevich@helmholtz-hips.de).

Your comments, bug reports, and suggestions are **very welcomed**.
They will help us to improve BGC-QUAST further.

If you have any troubles running BGC-QUAST, please attach `bgc-quast.log` from the output directory.

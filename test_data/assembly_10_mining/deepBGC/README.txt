DeepBGC
================================================================================
/home/akushnareva/miniconda3/envs/deepbgc/bin/deepbgc pipeline input/assembly_10.fasta.gz -o assembly_10_mining/deepBGC/
================================================================================
LOG.txt	Log output of DeepBGC
deepBGC.antismash.json 	AntiSMASH JSON file for sideloading.
deepBGC.bgc.gbk 	Sequences and features of all detected BGCs in GenBank format
deepBGC.bgc.tsv 	Table of detected BGCs and their properties
deepBGC.full.gbk 	Fully annotated input sequence with proteins, Pfam domains (PFAM_domain features) and BGCs (cluster features)
deepBGC.pfam.tsv 	Table of Pfam domains (pfam_id) from given sequence (sequence_id) in genomic order, with BGC detection scores
evaluation/deepBGC.bgc.png 	Detected BGCs plotted by their nucleotide coordinates
evaluation/deepBGC.pr.png 	Precision-Recall curve based on predicted per-Pfam BGC scores
evaluation/deepBGC.roc.png 	ROC curve based on predicted per-Pfam BGC scores
evaluation/deepBGC.score.png 	BGC detection scores of each Pfam domain in genomic order


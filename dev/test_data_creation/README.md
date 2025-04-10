# Test data creation 

## Obtaining genome sequences
The original genome sequence of *Streptomyces coelicolor* A3(2) was downloaded from https://www.ncbi.nlm.nih.gov/nuccore/NC_003888.3?report=fasta.
We then used `make_test_data.py` to trim first 1 Mbp into an artificial reference and to create two artificial assemblies out of it with 10 and 20 contigs named CONTIG_1, CONTIG_2, etc.

## Genome mining
### antiSMASH
We applied [the antiSMASH web server](https://antismash.secondarymetabolites.org/#!/start) using all default settings (as of 10.04.2025) 
plus "Enable antiSMASH v.8 beta" to the reference and both assemblies.
The corresponding output JSON files are in the `<sequence_filename>_mining/antiSMASH` directories.

### GECCO
TODO

### DeepBGC
TODO

## Assembly to reference alignment
We ran `quast -r reference.fasta assembly_10.fasta assembly_20.fasta -o quast_out --fast` to produce QUAST alignments for both assemblies. The results are in the `quast_out` directory.
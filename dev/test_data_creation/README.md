# Test data creation 

## Obtaining genome sequences
The original genome sequence of *Streptomyces coelicolor* A3(2) was downloaded from https://www.ncbi.nlm.nih.gov/nuccore/NC_003888.3?report=fasta.
We then used `make_test_data.py` to trim first 1 Mbp into an artificial reference and to create two artificial assemblies out of it with 10 and 20 contigs named CONTIG_1, CONTIG_2, etc.

## Genome mining
Complete outputs of all tools on one assembly are saved in `full_output_example/assembly_10_mining/`. The test data in the root directory contain only files essential for running BGC-QUAST. 

### antiSMASH
We applied [the antiSMASH web server](https://antismash.secondarymetabolites.org/#!/start) using all default settings (as of 10.04.2025) 
plus "Enable antiSMASH v.8 beta" to the reference and both assemblies.
The corresponding output JSON and GenBank files were compressed with GZIP and saved in the `<sequence_filename>_mining/antiSMASH` directories.

### GECCO
We applied [GECCO](https://github.com/zellerlab/GECCO) v0.9.10 using default settings (`gecco run --genome input_sequence -o output_dir`) to the reference genome and both assemblies. The corresponding outputs were saved in the `<sequence_filename>_mining/GECCO` directories.

### DeepBGC
We applied [deepBGC](https://github.com/Merck/deepbgc) v0.1.31 using default settings (`deepbgc pipeline input_sequence -o output_dir`) to the reference genome and both assemblies. The corresponding outputs were saved in the '<sequence_filename>_mining/deepBGC' directories.


## Assembly to reference alignment
We ran `quast -r reference.fasta assembly_10.fasta assembly_20.fasta -o quast_out --fast` to produce QUAST alignments for both assemblies. The results are in the `quast_out` directory.

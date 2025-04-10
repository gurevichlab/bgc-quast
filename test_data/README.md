# test_data

The data was produced from https://www.ncbi.nlm.nih.gov/nuccore/NC_003888.3?report=fasta using `make_test_data.py` to trim first 1 Mbp and create two artificial assemblies with 10 and 20 contigs named CONTIG_1, CONTIG_2, etc.

We ran [antismash](https://antismash.secondarymetabolites.org/#!/start) on the trimmed sequence and both assemblies: [sequence.json](sequence.json), [assembly_10.json](assembly_10.json), and [assembly_20.json](assembly_20.json). 

We ran `quast -r trimmed_sequence.fasta assembly_10.fasta assembly_20.fasta -o quast_out --fast` to produce quast alignments for both assemblies: [quast_out/](quast_out).
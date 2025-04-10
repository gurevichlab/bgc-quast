from Bio import SeqIO, Seq
from Bio.SeqRecord import SeqRecord
import random

test_data_file = 'sequence.fasta'

# Read the sequence and trim to 1Mbp
with open(test_data_file) as f:
    record = next(SeqIO.parse(f, "fasta"))
record.seq = record.seq[:1000000]

# Save trimmed sequence
with open('reference.fasta', 'w') as f:
    SeqIO.write(record, f, "fasta")


# Function to split sequence into n contigs
def split_into_contigs(record, n_contigs):
    seq = str(record.seq)

    # Calculate average contig size
    avg_size = len(seq) // n_contigs
    
    contigs = []
    pos = 0
    
    for i in range(n_contigs):
        # Vary contig size slightly around average
        if i < n_contigs - 1:
            size = avg_size + random.randint(-1000, 1000)
            contig = seq[pos:pos+size]
            pos += size
        else:
            # Last contig gets remainder
            contig = seq[pos:]
            
        record = SeqRecord(
            seq=Seq.Seq(contig),
            id=f"CONTIG_{i+1}",
            description=""
        )
        assert len(contig) > 0, f"Contig {i+1} is empty"
        contigs.append(record)
    
    return contigs

# Create 10 contig assembly
contigs_10 = split_into_contigs(record, 10)
with open("assembly_10.fasta", "w") as f:
    SeqIO.write(contigs_10, f, "fasta")

# Create 20 contig assembly  
contigs_20 = split_into_contigs(record, 20)
with open("assembly_20.fasta", "w") as f:
    SeqIO.write(contigs_20, f, "fasta")




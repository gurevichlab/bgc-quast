### Metrics description
metric | description | analysis mode
-------|-------------|----------------
`# BGCs filtered by length` | Number of BGCs shorter than the minimum length threshold that are excluded from the analysis | `compare-samples`
`# BGCs` | Total number of predicted BGCs that passed the length threshold | `compare-samples`
`Mean BGC length in bp` | Average BGC length in base pairs | `compare-samples`
`Mean BGC length in genes` | Average number of genes per BGC | `compare-samples`
`# full ref. BGCs` | Number of reference BGCs with ≥95% of their length covered by at least one assembly BGC | `compare-to-reference`
`# full ref. BGCs, single-contig` | Number of reference BGCs with ≥95% of their length covered by a single contiguous assembly BGC | `compare-to-reference`
`# full ref. BGCs, multi-contig` | Number of reference BGCs with ≥95% of their length covered by multiple disjoint assembly BGCs | `compare-to-reference`
`# partial ref. BGCs` | Number of reference BGCs with 10–95% of their length covered by one or more assembly BGCs | `compare-to-reference`
`# missed ref. BGCs` | Number of reference BGCs with <10% of their length covered by any assembly BGC | `compare-to-reference`
`Ref. BGC recovery rate` | Proportion of reference BGCs that are fully or partially recovered, regardless of product type | `compare-to-reference`
`# product type mismatches to ref.` | Number of assembly BGCs mapped to reference BGCs but predicted with a different product type | `compare-to-reference`
`# unmapped BGCs to ref.` | Number of assembly BGCs that do not map to any reference BGC | `compare-to-reference`
`# unique BGCs` | Number of BGCs detected by only one tool | `compare-tools`
`Unique BGC rate` | Proportion of BGCs detected by only one tool out of all BGCs predicted by that tool | `compare-tools`
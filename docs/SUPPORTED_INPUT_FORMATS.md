# Supported input formats

BGC-QUAST officially supports outputs from antiSMASH, GECCO, DeepBGC, and PRISM. Each parser reads only a small subset of the complete tool output.
The structures below show the fields needed to construct BGC records. Additional product information may be retained as metadata but is omitted here. Unrecognized product labels are reported as `Unknown product`.

## antiSMASH JSON

```text
records[]
├── id
└── features[]
    ├── type
    ├── location
    └── qualifiers              optional
        ├── product[]           optional
        └── region_number[]     optional
```

Only features with `type: region` are parsed as BGCs. Locations must follow the antiSMASH format:

```text
[start:end]
[start:end](+)
[start:end](-)
```

Coordinates are interpreted as 0-based and end-exclusive. Missing products are reported as `Unknown product`; if `region_number` is absent, `1` is used when constructing the BGC identifier.

Embedded `seq.data` and `gene` features may additionally be used to calculate sequence-dependent metrics when no separate genome file is supplied.

## GECCO TSV

The following columns are used:

```text
sequence_id
cluster_id
start
end
type
```

Multiple products in `type` must be separated by semicolons. GECCO coordinates are expected to be 1-based and end-inclusive; BGC-QUAST subtracts one from `start`.

When a product cannot be mapped, the following probability columns are also read to retain the closest product match as metadata:

```text
alkaloid_probability
nrp_probability
polyketide_probability
ripp_probability
saccharide_probability
terpene_probability
```

## DeepBGC TSV

The following columns are used:

```text
sequence_id
nucl_start
nucl_end
product_class
```

Coordinates are used directly as 0-based and end-exclusive. Multiple products in `product_class` must be separated by hyphens. Empty or unrecognized values are reported as `Unknown product`.

When a product cannot be mapped, the following class-probability columns are also read:

```text
Alkaloid
NRP
Other
Polyketide
RiPP
Saccharide
Terpene
```

## DeepBGC JSON

```text
records[]
├── name
└── subregions[]
    ├── start
    ├── end
    └── details                 optional
        └── product_class       optional
```

The top-level `records` field must be a list. Each subregion is parsed as one BGC, and coordinates are used directly as 0-based and end-exclusive. Multiple products in `product_class` must be separated by hyphens. Missing or unrecognized product classes are reported as `Unknown product`.

## PRISM JSON

Supported schema: PRISM 4.4.5.

```text
prism_results
└── clusters[]
    ├── contig
    ├── start
    ├── end
    └── type[]                  optional
```

Each cluster is parsed as one BGC. Coordinates are used directly as 0-based and end-exclusive. Missing or unrecognized product types are reported as `Unknown product`.
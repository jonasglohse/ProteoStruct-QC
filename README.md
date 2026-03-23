# ProteoStruct-QC

A Streamlit web app that connects public proteomics datasets to interactive 3D protein structure visualization. Enter a PRIDE accession to inspect dataset quality metrics, then map identified peptides onto an AlphaFold structure — all in one interface.

---

## What it does

**Dataset QC tab**
- Fetches project metadata (title, organism, instrument, submission date) from the PRIDE Archive
- Lists all files in the project and detects any `.mzQC` quality control files
- If an mzQC file is present, parses it and renders an interactive bar chart of QC metrics (MS1/MS2 scan counts, mass error, identification rate, etc.)
- If no mzQC file is present (common for most public submissions), allows manual upload of a local `.mzQC` file or loading of a built-in demo

**Structure Viewer tab**
- Search for proteins by name or gene via the UniProt search in the sidebar, or enter a UniProt ID directly
- Fetches the AlphaFold predicted structure for the selected protein
- User pastes a list of peptide sequences (one per line)
- Sequences are matched against the canonical UniProt protein sequence to resolve residue positions
- Matched peptides are highlighted on the 3D structure: green for standard peptides, magenta for PTM-bearing peptides (flagged with a `*` suffix)
- Toggle between plain grey and pLDDT confidence coloring (dark blue = very high, light blue = confident, yellow = low, orange = very low)
- A mapping table shows which peptides were found and at which residues

---

## Running the app

```bash
streamlit run app.py
```

Requires Python 3.10+ and the packages in `requirements.txt`.

```bash
pip install -r requirements.txt
```

---

## Repository structure

```
ProteoStruct-QC/
├── app.py                  # Streamlit app — single entry point
├── requirements.txt
│
├── modules/
│   ├── pride.py            # PRIDE Archive REST API v2 client
│   ├── qc.py               # mzQC JSON parser + Plotly chart builders
│   ├── structure.py        # AlphaFold fetch, UniProt sequence, peptide mapper
│   └── uniprot.py          # UniProt protein search client
│
├── data/
│   ├── demo.mzqc           # Built-in demo mzQC file with realistic metrics
│   └── demo_peptides.txt   # Pre-loaded peptide list for the Ubiquitin demo
│
├── PROJECT.md              # Project scope, build order, V1 success criteria
└── test_molstar.py         # Visualization smoke test (stmol + py3Dmol)
```

---

## Demo

- **PRIDE Demo:** loads `PXD070049` — LFQ Benchmark Dataset (timsTOF Ultra 2, Human/Yeast/E. coli)
- **QC Demo:** loads a synthetic mzQC file with representative scan count and mass error metrics
- **Structure Demo:** loads Human Ubiquitin (UniProt `P0CG48`) with pre-filled tryptic peptides

---

## Tech stack

| Concern | Library |
|---|---|
| UI | `streamlit` |
| 3D structure viewer | `stmol` + `py3Dmol` |
| PRIDE data access | direct PRIDE Archive REST API v2 via `requests` |
| QC parsing | mzQC JSON parsed directly (PSI standard format) |
| Charts | `plotly` |
| Data handling | `pandas` |
| Structure source | AlphaFold DB (by UniProt ID) |
| Sequence source | UniProt REST API |

---

## Notes

- mzQC files are rare in public PRIDE submissions; the manual upload path covers the common case where researchers have a local mzQC from their own analysis pipeline
- The PRIDE files API (`/projects/{accession}/files`) returns up to 100 files per request; pagination is not yet implemented
- AlphaFold coverage is broad but not universal; UniProt IDs without a prediction will return an error
- PTM site localization (coloring by modification site) requires the user to flag peptides manually with `*`; automatic PTM detection from identification files is a planned V2 feature

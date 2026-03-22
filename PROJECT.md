# ProteoStruct-QC

A Streamlit web app that connects public proteomics data to 3D protein structure visualization.

---

## What It Does

The user provides a PRIDE accession number and a UniProt ID. The app fetches QC metrics for the dataset and renders the 3D structure of the protein with user-supplied peptides highlighted on it. That's it.

---

## The Problem It Solves

Three useful things exist in isolation:
- Public MS datasets on PRIDE (accessible via `pridepy`)
- Standardized QC metrics in `.mzQC` files (readable via `pymzqc`)
- 3D protein structure viewers (`streamlit-molstar`)

No simple tool connects them. Researchers who want to quickly assess a public dataset and understand which parts of a protein were actually "seen" by the mass spectrometer have to jump between three separate tools manually. ProteoStruct-QC removes that friction.

---

## Scope: Version 1

### In

| Feature | Notes |
|---|---|
| PRIDE accession lookup | Fetch project metadata and file list via `pridepy` |
| mzQC parsing | Extract and plot key QC metrics (MS1/MS2 counts, mass error) using `pymzqc` + Plotly |
| Graceful fallback | If no `.mzQC` file exists, show a clear message and still allow the structural viewer |
| Manual peptide input | User pastes a list of peptide sequences into a text area |
| 3D structure fetch | Retrieve AlphaFold or PDB structure by UniProt ID |
| Peptide highlighting | Map pasted sequences onto the 3D structure via `streamlit-molstar` |
| PTM flag | User can mark peptides as PTM-bearing; those are colored distinctly |

### Out (future versions)

- Auto-parsing of PRIDE result files (MaxQuant, Spectronaut, mzIdentML)
- Peptide ambiguity scoring (MSCI logic)
- Koina spectral prediction overlay
- Multi-protein comparison

---

## Tech Stack

| Layer | Library |
|---|---|
| UI framework | `streamlit` |
| PRIDE data access | direct PRIDE Archive REST API v2 via `requests` |
| QC parsing | mzQC JSON parsed directly (PSI standard format) |
| 3D visualization | `stmol` + `py3Dmol` |
| Charts | `plotly` |
| Data handling | `pandas` |
| Structure fetch | AlphaFold DB REST API + stable file URL fallback |
| Sequence / protein search | UniProt REST API |

Python 3.10+. All dependencies installable via `pip`.

---

## App Layout

```
Sidebar
├── PRIDE Accession input         → triggers metadata + mzQC fetch
└── UniProt ID input              → triggers structure fetch

Main Panel
├── [Tab 1: Dataset QC]
│   ├── Project metadata (title, organism, instrument)
│   ├── mzQC metrics (bar/scatter charts via Plotly)
│   └── "No mzQC file found" notice if absent
│
└── [Tab 2: Structure Viewer]
    ├── streamlit-molstar 3D viewer
    ├── Peptide input text area (one sequence per line)
    ├── Checkbox: "Mark as PTM-bearing" per peptide
    └── Highlight button → maps sequences onto structure
```

---

## Color Convention for Peptide Highlighting

| Color | Meaning |
|---|---|
| Green | Standard identified peptide |
| Magenta | Peptide with PTM (user-flagged) |

Ambiguity scoring (red = maps to multiple proteins) is deferred to V2.

---

## Build Order

1. **Validate `stmol` + `py3Dmol` first.** Get a structure loading and a hardcoded peptide sequence highlighting before writing any other code. If this doesn't work, the project's visual centrepiece fails — better to know immediately.
2. **PRIDE metadata fetch.** Connect `pridepy`, display project title and file list. Check for `.mzQC` presence.
3. **mzQC parsing and charts.** Parse metrics with `pymzqc`, render with Plotly. Build the fallback state.
4. **Manual peptide input + highlighting.** Wire the text area to the `streamlit-molstar` sequence matching feature.
5. **Polish.** Layout, tab structure, error handling, the pre-loaded demo dataset (`PXD070049`).

---

## Demo Dataset

`PXD070049` — a high-throughput DIA benchmark (Human/Yeast/E. coli triple proteome). Well-documented, high-quality, publicly available. Used as the default "try it out" dataset on app load.

---

## Success Criteria for V1

- A user can enter a PRIDE accession and see project metadata within seconds.
- If an `.mzQC` file exists, at least two QC metrics are plotted interactively.
- A user can enter a UniProt ID and paste peptide sequences, and those sequences appear highlighted on the 3D structure.
- The app does not crash on accessions with no `.mzQC` file.

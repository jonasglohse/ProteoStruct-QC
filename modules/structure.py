"""
Structure fetching and peptide mapping.
- Structures: AlphaFold DB (primary)
- Sequences: UniProt REST API
"""
import requests


def get_alphafold_pdb(uniprot_id: str) -> str:
    """
    Fetch the AlphaFold predicted structure as a PDB string.
    Raises ValueError if no prediction exists for the given UniProt ID.
    """
    api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    r = requests.get(api_url, timeout=15)
    r.raise_for_status()
    predictions = r.json()

    if not predictions:
        raise ValueError(f"No AlphaFold prediction found for {uniprot_id}.")

    pdb_url = predictions[0].get("pdbUrl")
    if not pdb_url:
        raise ValueError(f"AlphaFold returned no PDB URL for {uniprot_id}.")

    r2 = requests.get(pdb_url, timeout=30)
    r2.raise_for_status()
    return r2.text


def get_protein_sequence(uniprot_id: str) -> str:
    """
    Fetch the canonical protein sequence from UniProt (FASTA format).
    Returns the sequence as a single uppercase string.
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    return "".join(line for line in lines if not line.startswith(">")).upper()


def map_peptides(sequence: str, raw_lines: list[str]) -> list[dict]:
    """
    Map peptide sequences onto a protein sequence.

    Input format (one per line):
        PEPTIDESEQ          → standard peptide (green)
        PEPTIDESEQ*         → PTM-bearing peptide (magenta)

    Returns a list of dicts:
        {peptide, start, end, found, ptm}
        start/end are 1-indexed residue numbers for py3Dmol.
    """
    results = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue

        ptm = line.endswith("*")
        peptide = line.rstrip("*").strip().upper()

        if not peptide:
            continue

        pos = sequence.find(peptide)
        if pos >= 0:
            results.append({
                "peptide": peptide,
                "start": pos + 1,
                "end": pos + len(peptide),
                "found": True,
                "ptm": ptm,
            })
        else:
            results.append({
                "peptide": peptide,
                "start": None,
                "end": None,
                "found": False,
                "ptm": ptm,
            })

    return results

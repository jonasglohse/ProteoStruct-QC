"""
Structure fetching and peptide mapping.
- Structures: AlphaFold DB (primary)
- Sequences: UniProt REST API
"""
import requests


def get_alphafold_pdb(uniprot_id: str) -> str:
    """
    Fetch the AlphaFold predicted structure as a PDB string.
    Tries the metadata API first; falls back to the direct stable file URL
    if the API returns a server error. Raises ValueError if no prediction exists.
    """
    api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    r = requests.get(api_url, timeout=15)

    if r.status_code == 404:
        raise ValueError(
            f"No AlphaFold structure available for {uniprot_id}. "
            "Try a different protein or enter the UniProt ID directly."
        )

    pdb_url = None
    if r.status_code == 200:
        predictions = r.json()
        if predictions:
            pdb_url = predictions[0].get("pdbUrl")

    if not pdb_url:
        # Fallback: construct the direct stable file URL (v4 model)
        pdb_url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"

    r2 = requests.get(pdb_url, timeout=30)
    if r2.status_code == 404:
        raise ValueError(
            f"No AlphaFold structure available for {uniprot_id}. "
            "Try a different protein or enter the UniProt ID directly."
        )
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

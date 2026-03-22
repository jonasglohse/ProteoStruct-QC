"""
UniProt REST API client.
Used for protein search and canonical sequence retrieval.
API docs: https://rest.uniprot.org
"""
import requests

_BASE = "https://rest.uniprot.org/uniprotkb"


def search_proteins(query: str, size: int = 15) -> list[dict]:
    """
    Search UniProtKB by protein name, gene name, or free text.
    Returns a list of lightweight protein summaries.
    """
    r = requests.get(
        f"{_BASE}/search",
        params={
            "query": query,
            "format": "json",
            "fields": "accession,protein_name,gene_names,organism_name,length",
            "size": size,
        },
        timeout=15,
    )
    r.raise_for_status()
    results = []
    for entry in r.json().get("results", []):
        results.append({
            "accession": entry.get("primaryAccession", ""),
            "protein_name": _extract_protein_name(entry),
            "gene": _extract_gene(entry),
            "organism": entry.get("organism", {}).get("scientificName", "N/A"),
            "length": entry.get("sequence", {}).get("length", "N/A"),
        })
    return results


def _extract_protein_name(entry: dict) -> str:
    desc = entry.get("proteinDescription", {})
    # Reviewed entries have recommendedName; unreviewed have submittedName
    recommended = desc.get("recommendedName", {})
    if recommended:
        return recommended.get("fullName", {}).get("value", "N/A")
    submitted = desc.get("submittedName", [])
    if submitted:
        return submitted[0].get("fullName", {}).get("value", "N/A")
    return "N/A"


def _extract_gene(entry: dict) -> str:
    genes = entry.get("genes", [])
    if genes:
        return genes[0].get("geneName", {}).get("value", "—")
    return "—"

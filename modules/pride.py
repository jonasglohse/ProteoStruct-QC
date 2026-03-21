"""
PRIDE Archive REST API v2 client.
All data comes from: https://www.ebi.ac.uk/pride/ws/archive/v2
"""
import requests

_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"


def search_projects(keyword: str, page_size: int = 25) -> list[dict]:
    """
    Search PRIDE Archive by keyword.
    Returns a list of lightweight project summaries.
    """
    r = requests.get(
        f"{_BASE}/projects",
        params={"keyword": keyword, "pageSize": page_size, "page": 0},
        timeout=15,
    )
    r.raise_for_status()
    projects = r.json() if r.text.strip() else []
    results = []
    for p in projects:
        organisms = ", ".join(o.get("name", "") for o in p.get("organisms", [])) or "N/A"
        instruments = ", ".join(i.get("name", "") for i in p.get("instruments", [])) or "N/A"
        results.append({
            "accession": p.get("accession", ""),
            "title": p.get("title", "N/A"),
            "organisms": organisms,
            "instruments": instruments,
            "submission_date": p.get("submissionDate", "N/A"),
        })
    return results


def get_project_metadata(accession: str) -> dict:
    r = requests.get(f"{_BASE}/projects/{accession}", timeout=15)
    r.raise_for_status()
    d = r.json()
    organisms = ", ".join(o.get("name", "") for o in d.get("organisms", [])) or "N/A"
    instruments = ", ".join(i.get("name", "") for i in d.get("instruments", [])) or "N/A"
    return {
        "title": d.get("title", "N/A"),
        "description": d.get("projectDescription", ""),
        "organisms": organisms,
        "instruments": instruments,
        "submission_date": d.get("submissionDate", "N/A"),
        "num_proteins": d.get("numberOfProteins"),
        "num_peptides": d.get("numberOfPeptides"),
    }


def get_project_files(accession: str) -> list:
    """
    Returns a list of file dicts, each augmented with a 'fileName' key
    extracted from the FTP URL for convenience.
    """
    r = requests.get(f"{_BASE}/projects/{accession}/files", timeout=15)
    r.raise_for_status()
    if not r.text.strip():
        return []
    try:
        files = r.json()
    except ValueError:
        return []
    # Augment each entry with a 'fileName' derived from its FTP/Aspera URL
    for f in files:
        f["fileName"] = _extract_filename(f)
    return files


def _extract_filename(file_entry: dict) -> str:
    for loc in file_entry.get("publicFileLocations", []):
        value = loc.get("value", "")
        if value:
            return value.rstrip("/").split("/")[-1]
    return ""


def find_mzqc_files(files: list) -> list:
    return [f for f in files if f.get("fileName", "").lower().endswith(".mzqc")]


def get_download_url(file_entry: dict) -> str | None:
    locations = file_entry.get("publicFileLocations", [])
    for preferred in ("FTP Protocol", "HTTPS Protocol", "Aspera Protocol"):
        for loc in locations:
            if loc.get("name") == preferred:
                return loc.get("value")
    return locations[0].get("value") if locations else None


def download_text(url: str) -> str:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.text

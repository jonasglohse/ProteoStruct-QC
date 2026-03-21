import streamlit as st
import py3Dmol
import pandas as pd
from stmol import showmol

from modules import pride, qc, structure

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ProteoStruct-QC",
    layout="wide",
)

DEMO_ACCESSION = "PXD070049"
DEMO_UNIPROT = "P0CG48"  # Human Ubiquitin
DEMO_PEPTIDES = open("data/demo_peptides.txt").read()

# ── Session state defaults ─────────────────────────────────────────────────────
for key, default in {
    "project": None,
    "files": None,
    "mzqc_metrics": None,
    "loaded_accession": None,
    "pdb_content": None,
    "protein_sequence": None,
    "loaded_uniprot": None,
    "peptide_mappings": None,
    "search_results": None,
    "search_triggered_accession": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("ProteoStruct-QC")
    st.caption("Proteomics QC + 3D Structure Explorer")

    st.divider()
    st.subheader("PRIDE Dataset")

    # Search
    with st.expander("Search PRIDE", expanded=False):
        search_query = st.text_input("Keywords", placeholder="e.g. DIA timsTOF human", key="search_query")
        search_btn = st.button("Search", use_container_width=True)
        if search_btn and search_query.strip():
            with st.spinner("Searching…"):
                try:
                    st.session_state["search_results"] = pride.search_projects(search_query.strip())
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    st.session_state["search_results"] = []

        if st.session_state["search_results"] is not None:
            results = st.session_state["search_results"]
            if not results:
                st.caption("No results found.")
            else:
                st.caption(f"{len(results)} result(s):")
                for r in results:
                    st.markdown(
                        f"**{r['accession']}** — {r['title'][:55]}{'…' if len(r['title']) > 55 else ''}  \n"
                        f"_{r['organisms']} · {r['submission_date']}_"
                    )
                    if st.button("Load this dataset", key=f"sr_{r['accession']}", use_container_width=True):
                        st.session_state["search_triggered_accession"] = r["accession"]
                        st.rerun()

    accession_input = st.text_input(
        "Accession", placeholder="e.g. PXD070049", key="accession_input"
    )
    col1, col2 = st.columns(2)
    load_pride = col1.button("Load", type="primary", use_container_width=True)
    demo_pride = col2.button("Demo", use_container_width=True)

    st.divider()
    st.subheader("Protein Structure")
    uniprot_input = st.text_input(
        "UniProt ID", placeholder="e.g. P0CG48", key="uniprot_input"
    )
    col3, col4 = st.columns(2)
    load_struct = col3.button("Load", type="primary", use_container_width=True, key="load_struct")
    demo_struct = col4.button("Demo", use_container_width=True, key="demo_struct")

# ── Resolve what to load this run ─────────────────────────────────────────────
accession_to_load = None
if st.session_state["search_triggered_accession"]:
    accession_to_load = st.session_state["search_triggered_accession"]
    st.session_state["search_triggered_accession"] = None
elif demo_pride:
    accession_to_load = DEMO_ACCESSION
elif load_pride and accession_input.strip():
    accession_to_load = accession_input.strip().upper()

uniprot_to_load = None
if demo_struct:
    uniprot_to_load = DEMO_UNIPROT
elif load_struct and uniprot_input.strip():
    uniprot_to_load = uniprot_input.strip().upper()

# ── Load PRIDE project ────────────────────────────────────────────────────────
if accession_to_load:
    with st.spinner(f"Fetching {accession_to_load} from PRIDE Archive…"):
        try:
            st.session_state["project"] = pride.get_project_metadata(accession_to_load)
            st.session_state["files"] = pride.get_project_files(accession_to_load)
            st.session_state["loaded_accession"] = accession_to_load
            st.session_state["mzqc_metrics"] = None

            mzqc_files = pride.find_mzqc_files(st.session_state["files"])
            if mzqc_files:
                url = pride.get_download_url(mzqc_files[0])
                if url:
                    with st.spinner("Downloading mzQC file…"):
                        json_text = pride.download_text(url)
                        st.session_state["mzqc_metrics"] = qc.parse_mzqc(json_text)
        except Exception as e:
            st.error(f"Could not load {accession_to_load}: {e}")

# ── Load structure ─────────────────────────────────────────────────────────────
if uniprot_to_load:
    with st.spinner(f"Fetching AlphaFold structure for {uniprot_to_load}…"):
        try:
            st.session_state["pdb_content"] = structure.get_alphafold_pdb(uniprot_to_load)
            st.session_state["protein_sequence"] = structure.get_protein_sequence(uniprot_to_load)
            st.session_state["loaded_uniprot"] = uniprot_to_load
            st.session_state["peptide_mappings"] = None
        except Exception as e:
            st.error(f"Could not load structure for {uniprot_to_load}: {e}")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_qc, tab_struct = st.tabs(["Dataset QC", "Structure Viewer"])

# ── Tab 1: Dataset QC ─────────────────────────────────────────────────────────
with tab_qc:
    if st.session_state["project"] is None:
        st.info("Enter a PRIDE accession in the sidebar and click **Load**, or try **Demo**.")
    else:
        proj = st.session_state["project"]
        files = st.session_state["files"]
        acc = st.session_state["loaded_accession"]

        st.header(proj["title"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Organism", proj["organisms"])
        c2.metric("Instrument", proj["instruments"])
        c3.metric("Submission Date", proj["submission_date"])

        if proj["num_proteins"] is not None:
            c4, c5 = st.columns(2)
            c4.metric("Proteins", f"{proj['num_proteins']:,}")
            c5.metric("Peptides", f"{proj['num_peptides']:,}")

        st.divider()

        mzqc_files = pride.find_mzqc_files(files or [])
        st.caption(
            f"{len(files or [])} file(s) in {acc} — "
            f"{len(mzqc_files)} mzQC file(s) found"
        )

        if st.session_state["mzqc_metrics"]:
            metrics = st.session_state["mzqc_metrics"]
            st.subheader("QC Metrics")

            for fig in qc.build_metrics_charts(metrics):
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("All metrics (full table)"):
                df = pd.DataFrame(metrics)[["run", "accession", "name", "value"]]
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            if not mzqc_files:
                st.warning("No .mzQC file found in this dataset — QC metrics are unavailable.")

            st.subheader("Load QC Metrics Manually")
            st.caption("Upload an .mzQC file from your local machine, or load the built-in demo.")

            col_up, col_demo_qc = st.columns([3, 1])
            uploaded = col_up.file_uploader("Upload .mzQC", type=["mzqc"], label_visibility="collapsed")
            load_demo_qc = col_demo_qc.button("Load QC Demo", use_container_width=True)

            if load_demo_qc:
                json_text = open("data/demo.mzqc").read()
                st.session_state["mzqc_metrics"] = qc.parse_mzqc(json_text)
                st.rerun()

            if uploaded is not None:
                try:
                    json_text = uploaded.read().decode("utf-8")
                    st.session_state["mzqc_metrics"] = qc.parse_mzqc(json_text)
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not parse mzQC file: {e}")

# ── Tab 2: Structure Viewer ────────────────────────────────────────────────────
with tab_struct:
    if st.session_state["pdb_content"] is None:
        st.info("Enter a UniProt ID in the sidebar and click **Load**, or try **Demo**.")
    else:
        uid = st.session_state["loaded_uniprot"]
        seq = st.session_state["protein_sequence"]
        st.caption(f"AlphaFold structure: {uid} — sequence length: {len(seq)} aa")

        # ── Peptide input ──────────────────────────────────────────────────────
        with st.form("peptide_form"):
            st.subheader("Peptide Sequences")
            st.caption(
                "One sequence per line. "
                "Append `*` to flag a PTM-bearing peptide (shown in magenta)."
            )

            default_text = DEMO_PEPTIDES if st.session_state["loaded_uniprot"] == DEMO_UNIPROT else ""
            peptide_text = st.text_area(
                "Sequences",
                value=default_text,
                height=160,
                placeholder="LIFAGKQLEDGR\nTLSDYNIQK*\nGILTLK",
                label_visibility="collapsed",
            )
            highlight = st.form_submit_button(
                "Highlight on Structure", type="primary", use_container_width=True
            )

        if highlight and peptide_text.strip():
            lines = peptide_text.strip().splitlines()
            mappings = structure.map_peptides(seq, lines)
            st.session_state["peptide_mappings"] = mappings

        # ── 3D Viewer ──────────────────────────────────────────────────────────
        mappings = st.session_state["peptide_mappings"] or []

        view = py3Dmol.view(width=900, height=540)
        view.addModel(st.session_state["pdb_content"], "pdb")
        view.setStyle({}, {"cartoon": {"color": "lightgrey", "opacity": 0.8}})

        for m in mappings:
            if m["found"]:
                color = "magenta" if m["ptm"] else "green"
                view.setStyle(
                    {"resi": f"{m['start']}-{m['end']}"},
                    {"cartoon": {"color": color}},
                )

        view.zoomTo()
        showmol(view, height=540, width=900)

        # ── Legend + mapping table ─────────────────────────────────────────────
        if mappings:
            found = [m for m in mappings if m["found"]]
            not_found = [m for m in mappings if not m["found"]]

            st.caption(
                f"{len(found)}/{len(mappings)} peptide(s) mapped.  "
                "🟢 Green = identified  |  🟣 Magenta = PTM-bearing"
            )
            if not_found:
                st.warning(
                    "Not found in sequence: "
                    + ", ".join(f"`{m['peptide']}`" for m in not_found)
                )

            with st.expander("Peptide mapping details"):
                rows = []
                for m in mappings:
                    rows.append({
                        "Peptide": m["peptide"],
                        "PTM": "yes" if m["ptm"] else "",
                        "Start": m["start"] if m["found"] else "—",
                        "End": m["end"] if m["found"] else "—",
                        "Found": "✓" if m["found"] else "✗",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

"""
Smoke test for stmol + py3Dmol.
Loads human Ubiquitin (PDB: 1UBQ) and highlights
one tryptic peptide: LIFAGKQLEDGR (residues 50-61) in green,
and one PTM-flagged peptide: TLSDYNIQK (residues 63-71) in magenta.
Run with: streamlit run test_molstar.py
"""
import streamlit as st
import py3Dmol
from stmol import showmol

st.title("stmol + py3Dmol smoke test")
st.write("Structure: Human Ubiquitin — PDB 1UBQ")

# Fetch structure from RCSB
view = py3Dmol.view(query="pdb:1UBQ", width=700, height=500)

# Base style: grey cartoon for the whole protein
view.setStyle({"cartoon": {"color": "grey"}})

# Green: standard identified peptide (residues 50-61)
view.setStyle({"resi": "50-61"}, {"cartoon": {"color": "green"}})

# Magenta: PTM-bearing peptide (residues 63-71)
view.setStyle({"resi": "63-71"}, {"cartoon": {"color": "magenta"}})

view.zoomTo()

showmol(view, height=500, width=700)

st.markdown("**Green** = standard peptide (res 50–61) | **Magenta** = PTM-bearing peptide (res 63–71)")

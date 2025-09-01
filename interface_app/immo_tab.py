import streamlit as st
import pandas as pd
from datetime import datetime

from modules_utils.ledger import read_ledger, append_entry
from modules_utils.audit import audit
from modules_utils.paths import IMMO_LOG

def render_immo():
    st.subheader("Immo (SCI / futur)")

    st.info("Placeholder : ajouter listing biens, rentabilité, échéances, etc.")

    st.markdown("### Compta & Logs (Immo)")
    df = read_ledger("immo")
    if df.empty:
        st.info("Aucune écriture dans data/immo_compta.csv")
    else:
        st.dataframe(df, use_container_width=True)
    if not df.empty:
        st.download_button(
            "Exporter Immo (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="immo_compta_export.csv",
            mime="text/csv",
        )
    # Ajout rapide d'une écriture (asset libre)
    col1, col2, col3 = st.columns(3)
    with col1:
        asset = st.text_input("Asset", value="Maison1")
    with col2:
        amount = st.number_input("Montant (€)", value=100, step=50)
    with col3:
        inout = st.selectbox("Type", ["income","expense"], index=0)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Ajouter écriture Immo"):
            append_entry("immo", {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": inout,
                "amount": float(amount),
                "currency": "EUR",
                "desc": "Saisie UI",
                "asset": asset,
            })
            st.toast("Écriture ajoutée à immo_compta.csv")
    with c2:
        if st.button("Test: + log Immo (INFO)"):
            audit("immo", "INFO", f"Test log asset {asset}")
            st.toast("Ligne ajoutée à logs/immo.log")

    # Log texte Immo
    try:
        text = IMMO_LOG.read_text(encoding="utf-8")
        st.text_area("immo.log", text, height=200)
    except FileNotFoundError:
        st.info("logs/immo.log inexistant pour l'instant.")

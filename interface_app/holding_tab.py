from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st
import yaml

from interface_app.holding_compta_logs import render_holding_compta_logs  # <- NEW

@st.cache_data(ttl=10)
def load_holding_config(path: str = "config/holding.yml") -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

@st.cache_data(ttl=10)
def load_prop_rules(path: str = "config/prop_rules.yml") -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"accounts": []}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"accounts": []}

@st.cache_data(ttl=10)
def load_equity_intraday(path: str = "data/equity_intraday.csv") -> Optional[pd.DataFrame]:
    p = Path(path)
    if not p.exists():
        return None
    df = pd.read_csv(p)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

@st.cache_data(ttl=10)
def load_trades_today(path: str = "data/trades_today.csv") -> Optional[pd.DataFrame]:
    p = Path(path)
    if not p.exists():
        return None
    return pd.read_csv(p)

def _build_tree_table(cfg: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if not cfg:
        return pd.DataFrame()
    holding = cfg.get("holding", {})
    children = cfg.get("children", []) or []
    rows.append({
        "id": holding.get("id"),
        "name": holding.get("name"),
        "legal_form": holding.get("legal_form"),
        "country": holding.get("country"),
        "parent": None,
        "role": holding.get("notes", "holding"),
        "level": 0,
    })
    for ch in children:
        rows.append({
            "id": ch.get("id"),
            "name": ch.get("name"),
            "legal_form": ch.get("legal_form"),
            "country": ch.get("country"),
            "parent": ch.get("parent"),
            "role": ch.get("role"),
            "level": 1,
        })
    return pd.DataFrame(rows)

def _aggregate_prop_kpis() -> Dict[str, Any]:
    rules = load_prop_rules()
    accounts = [a.get("id") for a in (rules.get("accounts") or []) if a.get("id")]
    eq_df = load_equity_intraday()
    tr_df = load_trades_today()

    total_equity = 0.0
    if eq_df is not None and not eq_df.empty and "timestamp" in eq_df.columns:
        for acc in accounts:
            sub = eq_df[eq_df.get("account_id", acc) == acc]
            if not sub.empty:
                sub = sub.sort_values("timestamp")
                total_equity += float(sub["equity"].iloc[-1])

    pnl_day = 0.0
    if tr_df is not None and not tr_df.empty and "pnl" in tr_df.columns:
        pnl_day = float(tr_df["pnl"].sum())

    return {
        "accounts_count": len(accounts),
        "total_equity": total_equity if total_equity > 0 else None,
        "pnl_day": pnl_day,
        "accounts": accounts,
    }

def render_holding():
    st.subheader("Holding (mère) & Filles")

    cfg = load_holding_config()
    if not cfg:
        st.error("config/holding.yml introuvable ou vide.")
        return

    holding = cfg.get("holding", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Holding", holding.get("name", "—"))
    col2.metric("Forme", holding.get("legal_form", "—"))
    col3.metric("Pays", holding.get("country", "—"))

    # KPIs agrégés prop
    st.markdown("#### KPIs agrégés (Prop)")
    agg = _aggregate_prop_kpis()
    k1, k2, k3 = st.columns(3)
    k1.metric("Comptes prop", agg["accounts_count"])
    k2.metric("Equity totale", f"{agg['total_equity']:,.0f} $" if agg["total_equity"] else "—")
    k3.metric("PnL (jour)", f"{agg['pnl_day']:,.0f} $")

    # Structure
    df = _build_tree_table(cfg)
    if not df.empty:
        st.markdown("#### Structure")
        df_view = df.copy()
        df_view["entity"] = df_view.apply(lambda r: ("  " * int(r["level"])) + f"• {r['name']}", axis=1)
        st.dataframe(
            df_view[["entity", "id", "legal_form", "country", "parent", "role"]],
            use_container_width=True
        )

    # Liens rapides (info-only)
    st.markdown("#### Comptes prop (liens rapides)")
    if agg["accounts"]:
        for acc in agg["accounts"]:
            st.button(f"Ouvrir Prop Firm · {acc}", help="Aller à l'onglet Prop Firm et choisir ce compte.")

    # Outils internes
    tools = cfg.get("tools", []) or []
    with st.expander("Outils internes (non juridiques)"):
        if tools:
            tdf = pd.DataFrame(tools)
            st.dataframe(tdf, use_container_width=True)
        else:
            st.info("Aucun outil déclaré.")

    st.caption("Les KPIs seront alimentés par les modules compta/prop/immo plus tard.")

    # === Compta & Logs consolidés (holding) ===
    render_holding_compta_logs()

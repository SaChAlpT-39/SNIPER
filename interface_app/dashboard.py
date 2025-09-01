import json
from pathlib import Path

import streamlit as st

from modules_utils.config_loader import ConfigLoader
from modules_utils.health import run_health_checks
from interface_app.propfirm_tab import render_propfirm
from interface_app.holding_tab import render_holding
from interface_app.immo_tab import render_immo
from interface_app.journal_tab import render_journal

st.set_page_config(page_title="SNIPER Dashboard", layout="wide")

if "auto_update" not in st.session_state:
    st.session_state["auto_update"] = False


@st.cache_data(ttl=10)
def load_all_configs():
    loader = ConfigLoader("config")
    risk = loader.load_risk()
    system = loader.load_system()
    api_limits = loader.load_api_limits()
    summary = loader.summarize_limits(api_limits)
    return risk, system, summary


def render_overview():
    st.subheader("Overview")
    left, right = st.columns([2, 1])
    risk, system, summary = load_all_configs()
    with left:
        st.markdown("#### System")
        st.json({"mode": system.mode, "logging_cfg": system.logging_cfg}, expanded=False)
        st.markdown("#### Risk")
        st.json(
            {
                "max_daily_dd_pct": risk.max_daily_dd_pct,
                "max_trade_r_pct": risk.max_trade_r_pct,
                "target_rr": risk.target_rr,
            },
            expanded=False,
        )
    with right:
        st.markdown("#### API limits (summary)")
        st.code(json.dumps(summary, indent=2), language="json")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Refresh"):
            load_all_configs.clear()
            st.experimental_rerun()
    with col2:
        st.session_state["auto_update"] = st.toggle("Auto-Update", value=st.session_state["auto_update"])


def render_trades():
    st.subheader("Trades (placeholder)")
    st.info("À brancher : table des trades (filters: date/symbol/side)")


def render_health():
    st.subheader("Health")
    if st.button("Re-check"):
        rpt = run_health_checks(Path("."))
        st.session_state["health"] = rpt.to_json()
    rpt_json = st.session_state.get("health", run_health_checks(Path(".")).to_json())
    st.code(rpt_json, language="json")


def main():
    tab_h, tab_prop, tab_immo, tab_journal, tab_over, tab_trades, tab_health = st.tabs(
        ["Holding", "Prop Firm", "Immo", "Journal", "Overview", "Trades", "Health"]
    )
    with tab_h:
        render_holding()
    with tab_prop:
        render_propfirm()
    with tab_immo:
        render_immo()
    with tab_journal:
        render_journal()
    with tab_over:
        render_overview()
    with tab_trades:
        render_trades()
    with tab_health:
        render_health()


if __name__ == "__main__":
    main()

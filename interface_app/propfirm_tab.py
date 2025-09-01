from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st
import yaml
from datetime import datetime, timedelta
import pytz

from modules_utils.ledger import read_ledger, append_entry
from modules_utils.audit import audit
from modules_utils.paths import PROP_LOG

PARIS = pytz.timezone("Europe/Paris")

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

def _time_until_reset(reset_time_str: str) -> Optional[str]:
    if not reset_time_str:
        return None
    try:
        now = datetime.now(PARIS)
        hh, mm = [int(x) for x in reset_time_str.split(":")]
        today_reset = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        target = today_reset if now <= today_reset else today_reset + timedelta(days=1)
        delta = target - now
        total_seconds = int(delta.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    except Exception:
        return None

def compute_kpis(account: Dict[str, Any], eq_df: Optional[pd.DataFrame], trades_df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    acc_id = account.get("id")
    rules  = account.get("rules", {}) or {}
    init_cap = float(account.get("initial_capital", 0.0))

    equity_now = None
    dd_current = None
    if eq_df is not None and not eq_df.empty:
        sub = eq_df[eq_df.get("account_id", acc_id) == acc_id].copy() if "account_id" in eq_df.columns else eq_df.copy()
        if not sub.empty:
            sub = sub.sort_values("timestamp")
            equity_now = float(sub["equity"].iloc[-1])
            peak = float(sub["equity"].max())
            dd_current = max(0.0, peak - float(sub["equity"].iloc[-1]))

    pnl_day = 0.0
    if trades_df is not None and not trades_df.empty:
        sub_t = trades_df[trades_df.get("account_id", acc_id) == acc_id]
        if "pnl" in sub_t.columns:
            pnl_day = float(sub_t["pnl"].sum())

    daily_loss_limit = float(rules.get("daily_loss_limit", 0.0))
    max_drawdown     = float(rules.get("max_drawdown", 0.0))

    margin_daily_left = daily_loss_limit - max(0.0, -pnl_day)
    margin_dd_left = None
    if dd_current is not None and max_drawdown > 0:
        margin_dd_left = max_drawdown - dd_current

    def pct_safe(numer, denom):
        if denom is None or denom <= 0:
            return None
        return max(0, min(100, int(round((numer / denom) * 100))))

    daily_pct = pct_safe(margin_daily_left, daily_loss_limit) if daily_loss_limit > 0 else None
    dd_pct = pct_safe(margin_dd_left, max_drawdown) if (max_drawdown and margin_dd_left is not None) else None

    return {
        "equity_now": equity_now,
        "pnl_day": pnl_day,
        "dd_current": dd_current,
        "daily_loss_limit": daily_loss_limit,
        "max_drawdown": max_drawdown,
        "margin_daily_left": margin_daily_left,
        "margin_dd_left": margin_dd_left,
        "daily_pct": daily_pct,
        "dd_pct": dd_pct,
    }

def render_prop_compta_logs(acc_id: str):
    st.markdown("### Compta & Logs (Prop)")

    # Table compta Prop filtrée par compte
    df = read_ledger("prop")
    if df.empty:
        st.info("Aucune écriture dans data/prop_compta.csv")
    else:
        if "account" in df.columns:
            df = df[df["account"] == acc_id]
        st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"Test: + écriture Prop ({acc_id}) +100$"):
            append_entry("prop", {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "income",
                "amount": 100,
                "currency": "USD",
                "desc": "Test income",
                "account": acc_id,
            })
            st.toast("Écriture ajoutée à prop_compta.csv")
    with col2:
        if st.button("Test: + log Prop (INFO)"):
            audit("prop", "INFO", f"Test log compte {acc_id}")
            st.toast("Ligne ajoutée à logs/prop.log")

    # Log texte Prop (aperçu)
    try:
        text = PROP_LOG.read_text(encoding="utf-8")
        st.text_area("prop.log", text, height=200)
    except FileNotFoundError:
        st.info("logs/prop.log inexistant pour l'instant.")

def render_propfirm():
    st.subheader("Prop Firm")

    rules_cfg = load_prop_rules()
    accounts = rules_cfg.get("accounts", []) or []
    if not accounts:
        st.error("config/prop_rules.yml introuvable ou vide (clé 'accounts').")
        return

    ids = [a.get("id") for a in accounts]
    acc_id = st.selectbox("Compte", ids, index=0)
    account = next(a for a in accounts if a.get("id") == acc_id)

    left, right = st.columns([2, 1])

    with right:
        st.markdown("#### Règles & Reset")
        st.json({
            "provider": account.get("provider"),
            "phase": account.get("phase"),
            "initial_capital": account.get("initial_capital"),
            "reset_time": account.get("reset_time"),
            "rules": account.get("rules"),
        }, expanded=False)
        reset_str = _time_until_reset(str(account.get("reset_time", "")))
        if reset_str:
            st.metric("Reset dans", reset_str)
        else:
            st.caption("Reset time non défini.")

    eq_df = load_equity_intraday()
    tr_df = load_trades_today()

    kpis = compute_kpis(account, eq_df, tr_df)
    with left:
        col1, col2, col3 = st.columns(3)
        col1.metric("Equity (now)", f"{kpis['equity_now']:,.0f} $" if kpis["equity_now"] is not None else "—")
        col2.metric("PnL (jour)", f"{kpis['pnl_day']:,.0f} $")
        dd_label = f"{kpis['dd_current']:,.0f} $" if kpis["dd_current"] is not None else "—"
        col3.metric("Drawdown actuel", dd_label)

        st.markdown("#### Marges avant violation")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"Daily loss restant: {kpis['margin_daily_left']:,.0f} $ / {kpis['daily_loss_limit']:,.0f} $")
            if kpis["daily_pct"] is not None:
                st.progress(kpis["daily_pct"], text=f"{kpis['daily_pct']}% restant")
            else:
                st.info("Daily loss non défini.")
        with c2:
            if kpis["margin_dd_left"] is not None and kpis["max_drawdown"] > 0:
                st.write(f"Max DD restant: {kpis['margin_dd_left']:,.0f} $ / {kpis['max_drawdown']:,.0f} $")
                st.progress(kpis["dd_pct"] or 0, text=f"{kpis['dd_pct'] or 0}% restant")
            else:
                st.info("Max DD non défini.")

    st.divider()

    st.markdown("#### Equity Curve (intraday)")
    if eq_df is not None and not eq_df.empty:
        sub = eq_df[eq_df.get("account_id", acc_id) == acc_id].copy() if "account_id" in eq_df.columns else eq_df.copy()
        if not sub.empty and "timestamp" in sub.columns:
            sub = sub.sort_values("timestamp").set_index("timestamp")
            st.line_chart(sub["equity"])
        else:
            st.info("Pas de lignes pour ce compte.")
    else:
        st.info("Aucune donnée d'equity intraday (data/equity_intraday.csv).")

    st.markdown("#### Trades du jour")
    if tr_df is not None and not tr_df.empty:
        sub_t = tr_df[tr_df.get("account_id", acc_id) == acc_id].copy() if "account_id" in tr_df.columns else tr_df.copy()
        st.dataframe(sub_t, use_container_width=True)
    else:
        st.info("Aucun trade du jour (data/trades_today.csv).")

    st.divider()

    # === Compta & Logs prop (filtrés par compte) ===
    render_prop_compta_logs(acc_id)

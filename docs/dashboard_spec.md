# SNIPER — Dashboard Spec (v0)

## 0) But
Avoir un tableau de bord minimal, stable et utile **dès aujourd’hui**, basé sur ce qu’on a déjà en code :
- Configs (system/risk/api_limits) via `ConfigLoader`
- Health-check via `run_health_checks`
- Logging opérationnel
- (placeholder) zone Trades

## 1) Structure des onglets

### A. Overview
**Données**
- System: `mode`, `logging_cfg`
- Risk: `max_daily_dd_pct`, `max_trade_r_pct`, `target_rr`
- API limits (résumé): output de `ConfigLoader.summarize_limits()`

**UI**
- 2 colonnes : 
  - Gauche = System + Risk (cartes simples)
  - Droite = API limits (bloc JSON ou table)
- Barre d’actions: `Refresh`, `Auto-Update (toggle)`

**Critère d’acceptation**
- Je vois les 3 blocs (System/Risk/API limits)
- Le bouton Refresh recharge les configs

### B. Trades (placeholder)
**Données**
- (À venir) table des trades depuis DB/CSV

**UI**
- Filtres: date (jour), symbole, side
- Table: colonnes `time, symbol, side, size, R, PnL`
- (Plus tard) Export CSV

**Critère d’acceptation**
- Une table s’affiche (même vide) + les filtres existent

### C. Health
**Données**
- `run_health_checks(Path("."))` → rapport json { ok, details }

**UI**
- Carte statut global (OK/FAIL)
- Détail key/value (config_dir, logs_dir, logs_writable, disk_space, etc.)
- Bouton `Re-check`

**Critère d’acceptation**
- Je clique `Re-check` et la vue se met à jour

## 2) Sources de données (phase actuelle)
- `modules_utils/config_loader.py` (Pydantic) → system/risk/api_limits
- `modules_utils/health.py` → health report
- `logs/system.log` (juste pour vérifier que l’écriture est ok)

## 3) Techniques (framework & style)
- Framework: **Streamlit**
- Mise en page: `st.tabs`, `st.columns`, `st.dataframe`, `st.code/st.json`
- Thème: dark (optionnel), largeur: `layout="wide"`
- Comportement: `@st.cache_data(ttl=10)` pour les lectures “lentes”
- Refresh: bouton + toggle `Auto-Update` (poll léger plus tard)

## 4) Plus tard — Prop Firm View (v1 à venir)
- Comptes: nom, phase (challenge/verification/funded), capital
- Règles: daily loss limit, max drawdown, trailing vs static
- KPIs temps réel: equity, PnL du jour, % rule left, compte à rebours reset quotidien
- Graphique equity curve (jour/semaine/mois)
- Alertes Telegram si seuils approchés
- Intégration provider (API prop firm ou parsing via mail/bot → TBD)

## 5) Acceptation globale v0
- Lancer: `streamlit run interface_app/dashboard.py`
- Je vois 3 onglets (Overview/Trades/Health)
- Overview affiche config & API limits
- Health réagit au bouton `Re-check`
- Aucun crash si `api_limits` change (les clés sont optionnelles côté loader)

## 6) Fichiers concernés (après spec)
- `interface_app/dashboard.py` (squelette Streamlit)
- `docs/ui_cheatsheet.md` (déjà fait)
- `docs/dashboard_spec.md` (ce fichier)


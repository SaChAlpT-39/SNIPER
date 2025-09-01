import sys, os
# Ajoute la racine du projet (dossier SNIPER) au sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

modules = [
    "sniper_engine.api_handler",
    "sniper_engine.risk_manager",
    "sniper_engine.trading",
    "sniper_engine.utils",
    "orderflow.dom_reader",
    "orderflow.liquidity_map",
    "trap_simulator.trap_decoder",
    "vectorx.vectorx",
    "sentiment_macro.news_parser",
    "sniper_compta.comptabilite",
    "journal_ia.journal_ai",
    "interface_app.dashboard",
    "modules_utils.log_db_writer",
]
for m in modules:
    try:
        __import__(m)
        print(m, "=> OK")
    except Exception as e:
        print(m, "=> FAIL:", e)

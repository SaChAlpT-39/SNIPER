import json
import logging, logging.config
from pathlib import Path

import yaml

from modules_utils.config_loader import ConfigLoader
from modules_utils.rate_limiter import RateLimiter
from modules_utils.health import run_health_checks   # ← NEW

def setup_logging(cfg_path: Path = Path("config/logging.yml")):
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logging.config.dictConfig(cfg)

def main():
    setup_logging()
    log = logging.getLogger("sniper")
    log.info("boot: starting SNIPER")

    # --- Load configs ---
    loader = ConfigLoader("config")
    risk = loader.load_risk()
    system = loader.load_system()
    api_limits = loader.load_api_limits()
    summary = loader.summarize_limits(api_limits)

    log.info(f"system: mode={system.mode}, logging_cfg={system.logging_cfg}")
    log.info(f"risk: dd={risk.max_daily_dd_pct}%, r/trade={risk.max_trade_r_pct}%, targetRR={risk.target_rr}")
    log.info("api_limits: " + json.dumps(summary, ensure_ascii=False))

    # --- Health checks (watchdog) ---
    report = run_health_checks(Path("."))
    if report.ok:
        log.info("health: OK")
    else:
        log.error("health: FAIL")
    for k, v in report.details.items():
        log.info(f"health::{k} => {v}")

    # --- Rate limiter demo (kept) ---
    rl = RateLimiter()
    rl.set_limit_from_summary('binance.futures', summary, burst=40)
    rl.call('binance.futures', cost=5)
    log.info("rate_limiter: first weighted call (binance.futures cost=5) passed")

    print("SNIPER boot OK. See logs/system.log and console.")
    return 0 if report.ok else 1

if __name__ == "__main__":
    raise SystemExit(main())

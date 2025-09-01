import json
import logging, logging.config
from pathlib import Path

import yaml

from modules_utils.config_loader import ConfigLoader

def setup_logging(cfg_path: Path = Path("config/logging.yml")):
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logging.config.dictConfig(cfg)

def main():
    setup_logging()
    log = logging.getLogger("sniper")
    log.info("boot: starting SNIPER")

    loader = ConfigLoader("config")
    risk = loader.load_risk()
    system = loader.load_system()
    api_limits = loader.load_api_limits()
    summary = loader.summarize_limits(api_limits)

    log.info(f"system: mode={system.mode}, logging_cfg={system.logging_cfg}")
    log.info(f"risk: dd={risk.max_daily_dd_pct}%, r/trade={risk.max_trade_r_pct}%, targetRR={risk.target_rr}")
    log.info("api_limits: " + json.dumps(summary, ensure_ascii=False))

    print("SNIPER boot OK. See logs/system.log and console.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

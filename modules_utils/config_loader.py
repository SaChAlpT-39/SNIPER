from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, ConfigDict


# --------- Pydantic models ---------

class RiskModel(BaseModel):
    max_daily_dd_pct: float = Field(..., ge=0)
    max_trade_r_pct: float = Field(..., ge=0)
    target_rr: float = Field(..., gt=0)

class SystemModel(BaseModel):
    mode: Literal["dev", "live", "backtest"] = "dev"
    logging_cfg: str = "config/logging.yml"

class BinanceSpotLimits(BaseModel):
    requests_per_min: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None

class BinanceFuturesLimits(BaseModel):
    requests_per_min: Optional[int] = Field(default=None, ge=0)
    orders_per_min: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None

class BinanceLimits(BaseModel):
    spot: Optional[BinanceSpotLimits] = None
    futures: Optional[BinanceFuturesLimits] = None

class TelegramLimits(BaseModel):
    per_chat_rps: Optional[float] = Field(default=None, ge=0)
    per_group_rpm: Optional[int] = Field(default=None, ge=0)
    global_rps: Optional[float] = Field(default=None, ge=0)

class NewsAPILimits(BaseModel):
    requests_per_day: Optional[int] = Field(default=None, ge=0)
    burst_rps: Optional[float] = Field(default=None, ge=0)

class FredLimits(BaseModel):
    requests_per_min: Optional[int] = Field(default=None, ge=0)

class YahooProviderLimits(BaseModel):
    name: Optional[str] = None
    requests_per_min: Optional[int] = Field(default=None, ge=0)
    requests_per_day: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None

class GNewsLimits(BaseModel):
    requests_per_day: Optional[int] = Field(default=None, ge=0)
    burst_rps: Optional[float] = Field(default=None, ge=0)

class NewsdataLimits(BaseModel):
    requests_per_15min: Optional[int] = Field(default=None, ge=0)
    requests_per_min: Optional[float] = Field(default=None, ge=0)

class APILimits(BaseModel):
    # On permet des clés supplémentaires pour pouvoir ajouter d'autres APIs plus tard.
    model_config = ConfigDict(extra="allow")

    binance: Optional[BinanceLimits] = None
    telegram: Optional[TelegramLimits] = None
    newsapi: Optional[NewsAPILimits] = None
    fred: Optional[FredLimits] = None
    yahoo_provider: Optional[YahooProviderLimits] = None
    gnews: Optional[GNewsLimits] = None
    newsdata: Optional[NewsdataLimits] = None


# --------- Loader ---------

class ConfigLoader:
    def __init__(self, config_dir: str | Path = "config"):
        self.config_dir = Path(config_dir)

    def _load_yaml(self, name: str) -> Dict[str, Any]:
        path = self.config_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_risk(self) -> RiskModel:
        data = self._load_yaml("risk.yml")
        try:
            return RiskModel(**(data.get("risk") or {}))
        except ValidationError as e:
            raise ValueError(f"Invalid risk.yml: {e}") from e

    def load_system(self) -> SystemModel:
        data = self._load_yaml("system.yml")
        try:
            return SystemModel(**(data.get("system") or {}))
        except ValidationError as e:
            raise ValueError(f"Invalid system.yml: {e}") from e

    def load_api_limits(self) -> APILimits:
        data = self._load_yaml("api_limits.yml")
        try:
            return APILimits(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid api_limits.yml: {e}") from e

    # Helpers de normalisation (comme avant)
    @staticmethod
    def rpm_to_rps(rpm: Optional[float | int]) -> Optional[float]:
        if rpm is None:
            return None
        return max(0.0, float(rpm) / 60.0)

    @staticmethod
    def per_15min_to_rpm(v: Optional[float | int]) -> Optional[float]:
        if v is None:
            return None
        return float(v) / 15.0

    def summarize_limits(self, api: APILimits) -> Dict[str, Any]:
        out: Dict[str, Any] = {}

        # Binance
        if api.binance:
            out["binance"] = {}
            if api.binance.spot:
                rpm = api.binance.spot.requests_per_min
                out["binance"]["spot"] = {"rpm": rpm, "rps": self.rpm_to_rps(rpm)}
            if api.binance.futures:
                rpm = api.binance.futures.requests_per_min
                out["binance"]["futures"] = {"rpm": rpm, "rps": self.rpm_to_rps(rpm)}

        # Telegram
        if api.telegram:
            out["telegram"] = api.telegram.model_dump()

        # NewsAPI
        if api.newsapi:
            out["newsapi"] = api.newsapi.model_dump()

        # FRED
        if api.fred:
            rpm = api.fred.requests_per_min
            out["fred"] = {"rpm": rpm, "rps": self.rpm_to_rps(rpm)}

        # Yahoo provider
        if api.yahoo_provider:
            y = api.yahoo_provider
            out["yahoo_provider"] = {
                "name": y.name,
                "rpm": y.requests_per_min,
                "rps": self.rpm_to_rps(y.requests_per_min),
                "per_day": y.requests_per_day,
            }

        # Newsdata
        if api.newsdata:
            nd_rpm = api.newsdata.requests_per_min
            if nd_rpm is None and api.newsdata.requests_per_15min is not None:
                nd_rpm = self.per_15min_to_rpm(api.newsdata.requests_per_15min)
            out["newsdata"] = {"rpm": nd_rpm, "rps": self.rpm_to_rps(nd_rpm)}

        return out


def _main():
    loader = ConfigLoader("config")
    risk = loader.load_risk()
    system = loader.load_system()
    api_limits = loader.load_api_limits()
    summary = loader.summarize_limits(api_limits)

    print("== RISK ==", risk)
    print("== SYSTEM ==", system)
    print("== SUMMARY ==", summary)

if __name__ == "__main__":
    _main()

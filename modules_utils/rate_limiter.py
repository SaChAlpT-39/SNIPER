from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from math import ceil
from threading import Lock
from typing import Dict, Optional


@dataclass
class _Bucket:
    rps: float
    capacity: float
    tokens: float
    last: float
    lock: Lock

    def refill(self) -> None:
        now = time.monotonic()
        dt = now - self.last
        if dt <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + dt * self.rps)
        self.last = now

    def acquire(self, cost: float = 1.0) -> None:
        # Bloc jusqu'à ce qu'on ait assez de tokens.
        while True:
            with self.lock:
                self.refill()
                if self.tokens >= cost:
                    self.tokens -= cost
                    return
                # pas assez de tokens -> sleep le temps nécessaire
                missing = cost - self.tokens
                sleep_for = missing / self.rps if self.rps > 0 else 0.05
            time.sleep(max(0.01, sleep_for))


class RateLimiter:
    """
    Exemple d'usage:
      rl = RateLimiter()
      rl.set_limit('binance.futures', rps=40, burst=40)
      rl.call('binance.futures', cost=5)   # endpoint weight=5
    """
    def __init__(self) -> None:
        self._buckets: Dict[str, _Bucket] = {}

    @staticmethod
    def _mk_bucket(rps: float, burst: Optional[int]) -> _Bucket:
        # Burst = capacité max de tokens (par défaut ~1 seconde de tokens)
        capacity = float(burst if burst is not None else max(1, ceil(rps)))
        return _Bucket(
            rps=max(0.001, float(rps)),
            capacity=capacity,
            tokens=capacity,              # start full
            last=time.monotonic(),
            lock=Lock(),
        )

    def set_limit(self, key: str, *, rps: float, burst: Optional[int] = None) -> None:
        self._buckets[key] = self._mk_bucket(rps, burst)

    def call(self, key: str, *, cost: float = 1.0) -> None:
        if key not in self._buckets:
            # sécurité : si non configuré -> très lent (0.5 rps)
            self.set_limit(key, rps=0.5, burst=1)
        self._buckets[key].acquire(cost=cost)

    # ---------- Helpers d’intégration avec ConfigLoader ----------

    def set_limit_from_summary(self, key: str, summary: dict, *, default_rps: float = 1.0, burst: Optional[int] = None) -> None:
        """
        key ex: 'binance.spot' / 'binance.futures' / 'fred'...
        summary = loader.summarize_limits(api_limits)
        """
        parts = key.split(".")
        node = summary
        for p in parts:
            node = node.get(p, {})
        # on cherche d'abord 'rps', sinon on devine depuis 'rpm'
        rps = node.get("rps")
        if rps is None:
            rpm = node.get("rpm")
            if rpm is not None:
                rps = float(rpm) / 60.0
        if rps is None:
            rps = default_rps
        self.set_limit(key, rps=float(rps), burst=burst)

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from config import DATA_DIR, ensure_directories


class CostCircuitBreakerStore:
    def __init__(self) -> None:
        ensure_directories()
        self._path = Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR))) / 'cost-circuit-breaker.json'

    def get_config(self) -> dict[str, Any]:
        path = self._effective_path()
        if not path.exists():
            return {'max_actual_cost_usd': None, 'max_total_tokens': None}
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return {'max_actual_cost_usd': None, 'max_total_tokens': None}
        if not isinstance(payload, dict):
            return {'max_actual_cost_usd': None, 'max_total_tokens': None}
        return {
            'max_actual_cost_usd': payload.get('max_actual_cost_usd'),
            'max_total_tokens': payload.get('max_total_tokens'),
        }

    def update_config(self, *, max_actual_cost_usd: float | None, max_total_tokens: int | None) -> dict[str, Any]:
        path = self._effective_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'max_actual_cost_usd': max_actual_cost_usd,
            'max_total_tokens': max_total_tokens,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return payload

    def evaluate(self, *, totals: dict[str, Any]) -> dict[str, Any]:
        config = self.get_config()
        reasons: list[str] = []
        actual_cost = float(totals.get('actual_cost_usd') or 0.0)
        total_tokens = int(totals.get('total_tokens') or 0)
        max_cost = config.get('max_actual_cost_usd')
        max_tokens = config.get('max_total_tokens')
        if isinstance(max_cost, (int, float)) and actual_cost > float(max_cost):
            reasons.append('cost_limit_exceeded')
        if isinstance(max_tokens, int) and total_tokens > max_tokens:
            reasons.append('token_limit_exceeded')
        return {
            'config': config,
            'tripped': bool(reasons),
            'reasons': reasons,
        }

    def _effective_path(self) -> Path:
        return Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR))) / 'cost-circuit-breaker.json'


cost_circuit_breaker_store = CostCircuitBreakerStore()

from __future__ import annotations

from cost_controls import cost_circuit_breaker_store
from http_api import route
from usage_surface import usage_surface


def _build_panel_usage(summary: dict) -> dict:
    totals = summary.get('totals', {})
    breaker = summary.get('circuit_breaker', {})
    breaker_config = breaker.get('config', {})
    agents = summary.get('agent_breakdown', [])

    budget = breaker_config.get('max_actual_cost_usd')
    if not isinstance(budget, (int, float)) or budget <= 0:
        budget = 10.00
    max_tokens = breaker_config.get('max_total_tokens')
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        max_tokens = 1500000

    return {
        'today': {
            'tokens': totals.get('total_tokens', 0),
            'cost': totals.get('actual_cost_usd', 0.0),
            'budget': budget,
            'sessions': totals.get('session_count', 0),
            'requests': totals.get('session_count', 0),
        },
        'breaker': {
            'tripped': breaker.get('tripped', False),
            'maxCost': budget,
            'maxTokens': max_tokens,
        },
        'agents': [
            {
                'id': a.get('agent_id', ''),
                'tokens': a.get('total_tokens', 0),
                'cost': a.get('actual_cost_usd', 0.0),
                'sessions': a.get('session_count', 0),
            }
            for a in agents
        ],
        'hourly': [],
    }


@route('GET', '/ops/usage', allow=('GET',))
def ops_usage(handler) -> None:
    summary = usage_surface.summary()
    handler.send_panel_data(summary, panel=_build_panel_usage(summary))

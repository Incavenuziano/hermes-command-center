from __future__ import annotations

from cost_controls import cost_circuit_breaker_store
from release_hardening import release_hardening
from runtime_adapter import runtime_adapter


def _usage_cost_payload() -> dict[str, object]:
    sessions = runtime_adapter.list_sessions()
    agents: dict[str, dict[str, object]] = {}
    totals = {
        'session_count': len(sessions),
        'input_tokens': 0,
        'output_tokens': 0,
        'reasoning_tokens': 0,
        'total_tokens': 0,
        'estimated_cost_usd': 0.0,
        'actual_cost_usd': 0.0,
    }
    for session in sessions:
        agent_id = str(session.get('agent_id') or 'agent-main')
        agent = agents.setdefault(agent_id, {
            'agent_id': agent_id,
            'session_count': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'reasoning_tokens': 0,
            'total_tokens': 0,
            'estimated_cost_usd': 0.0,
            'actual_cost_usd': 0.0,
        })
        agent['session_count'] += 1
        for key in ('input_tokens', 'output_tokens', 'reasoning_tokens'):
            value = int(session.get(key) or 0)
            totals[key] += value
            agent[key] += value
        total_tokens = int(session.get('input_tokens') or 0) + int(session.get('output_tokens') or 0) + int(session.get('reasoning_tokens') or 0)
        totals['total_tokens'] += total_tokens
        agent['total_tokens'] += total_tokens
        for key in ('estimated_cost_usd', 'actual_cost_usd'):
            value = float(session.get(key) or 0.0)
            totals[key] += value
            agent[key] += value
    return {'totals': totals, 'agents': list(agents.values()), 'circuit_breaker': cost_circuit_breaker_store.evaluate(totals=totals)}


class UsageSurface:
    def summary(self) -> dict[str, object]:
        cost_payload = _usage_cost_payload()
        sessions = runtime_adapter.list_sessions()
        top_sessions = sorted(
            sessions,
            key=lambda item: (float(item.get('actual_cost_usd') or 0.0), int(item.get('input_tokens') or 0) + int(item.get('output_tokens') or 0) + int(item.get('reasoning_tokens') or 0)),
            reverse=True,
        )[:5]
        performance = release_hardening.performance_snapshot()
        load_smoke = release_hardening.load_smoke()
        breaker = cost_payload['circuit_breaker']
        totals = cost_payload['totals']
        summary_cards = [
            {'label': 'Total Tokens', 'value': totals['total_tokens'], 'tone': 'neutral'},
            {'label': 'Actual Cost USD', 'value': totals['actual_cost_usd'], 'tone': 'neutral'},
            {'label': 'Circuit Breaker', 'value': 'tripped' if breaker.get('tripped') else 'healthy', 'tone': 'danger' if breaker.get('tripped') else 'success'},
            {'label': 'Load Smoke Failures', 'value': load_smoke.get('failures', 0), 'tone': 'danger' if load_smoke.get('failures', 0) else 'success'},
        ]
        return {
            'totals': totals,
            'agent_breakdown': cost_payload['agents'],
            'circuit_breaker': breaker,
            'performance': performance,
            'load_smoke': load_smoke,
            'top_sessions': top_sessions,
            'summary_cards': summary_cards,
        }


usage_surface = UsageSurface()

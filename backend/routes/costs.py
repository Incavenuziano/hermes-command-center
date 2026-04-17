from __future__ import annotations

from cost_controls import cost_circuit_breaker_store
from http_api import RequestValidationError, route
from runtime_adapter import runtime_adapter


def _cost_payload() -> dict[str, object]:
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
    agent_list = list(agents.values())
    breaker = cost_circuit_breaker_store.evaluate(totals=totals)
    return {'totals': totals, 'agents': agent_list, 'circuit_breaker': breaker}


@route('GET', '/ops/costs', allow=('GET',))
def ops_costs(handler) -> None:
    handler.send_data(_cost_payload())


@route('POST', '/ops/costs/circuit-breaker', allow=('POST',))
def ops_costs_circuit_breaker(handler) -> None:
    payload = handler.read_json_body()
    max_cost = payload.get('max_actual_cost_usd')
    max_tokens = payload.get('max_total_tokens')
    if max_cost is not None and not isinstance(max_cost, (int, float)):
        raise RequestValidationError(status=400, code='ops.invalid_request', message='max_actual_cost_usd must be numeric', details={'field': 'max_actual_cost_usd'})
    if max_tokens is not None and not isinstance(max_tokens, int):
        raise RequestValidationError(status=400, code='ops.invalid_request', message='max_total_tokens must be an integer', details={'field': 'max_total_tokens'})
    config = cost_circuit_breaker_store.update_config(
        max_actual_cost_usd=float(max_cost) if max_cost is not None else None,
        max_total_tokens=max_tokens,
    )
    snapshot = _cost_payload()
    handler.send_data({'config': config, 'circuit_breaker': snapshot['circuit_breaker']})

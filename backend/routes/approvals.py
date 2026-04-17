from __future__ import annotations

from approvals import approvals_store
from derived_state import derived_state_store
from http_api import RequestValidationError, route


@route('GET', '/ops/approvals', allow=('GET',))
def list_approvals(handler) -> None:
    handler.send_data(approvals_store.list_items())


@route('POST', '/ops/approvals', allow=('POST',))
def create_approval(handler) -> None:
    payload = handler.read_json_body()
    kind = payload.get('kind')
    title = payload.get('title')
    summary = payload.get('summary')
    source = payload.get('source', 'command-center')
    choices = payload.get('choices', [])
    if not isinstance(kind, str) or not kind:
        raise RequestValidationError(status=400, code='approval.invalid_request', message='kind is required', details={'field': 'kind'})
    if not isinstance(title, str) or not title:
        raise RequestValidationError(status=400, code='approval.invalid_request', message='title is required', details={'field': 'title'})
    if not isinstance(summary, str) or not summary:
        raise RequestValidationError(status=400, code='approval.invalid_request', message='summary is required', details={'field': 'summary'})
    if not isinstance(source, str) or not source:
        raise RequestValidationError(status=400, code='approval.invalid_request', message='source is required', details={'field': 'source'})
    if not isinstance(choices, list) or not all(isinstance(item, str) for item in choices):
        raise RequestValidationError(status=400, code='approval.invalid_request', message='choices must be a list of strings', details={'field': 'choices'})
    item = approvals_store.enqueue(kind=kind, title=title, summary=summary, source=source, choices=choices)
    derived_state_store.ingest_event({'kind': 'approval.created', 'source': source, 'data': {'approval_id': item['id'], 'status': item['status'], 'kind': kind}})
    handler.send_data({'item': item})


@route('POST', '/ops/approvals/resolve', allow=('POST',))
def resolve_approval(handler) -> None:
    payload = handler.read_json_body()
    item_id = payload.get('item_id')
    decision = payload.get('decision')
    if not isinstance(item_id, str) or not item_id:
        raise RequestValidationError(status=400, code='approval.invalid_request', message='item_id is required', details={'field': 'item_id'})
    if not isinstance(decision, str) or not decision:
        raise RequestValidationError(status=400, code='approval.invalid_request', message='decision is required', details={'field': 'decision'})
    try:
        item = approvals_store.resolve(item_id=item_id, decision=decision)
    except KeyError as exc:
        raise RequestValidationError(status=404, code='approval.not_found', message='Approval item not found', details={'item_id': item_id}) from exc
    derived_state_store.ingest_event({'kind': 'approval.resolved', 'source': 'command-center', 'data': {'approval_id': item['id'], 'status': item['status'], 'decision': decision}})
    handler.send_data({'item': item})

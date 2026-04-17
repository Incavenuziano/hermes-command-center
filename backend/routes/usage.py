from __future__ import annotations

from http_api import route
from usage_surface import usage_surface


@route('GET', '/ops/usage', allow=('GET',))
def ops_usage(handler) -> None:
    handler.send_data(usage_surface.summary())

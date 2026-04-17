from __future__ import annotations

from design_advisor import hcc_design_advisor
from http_api import route


@route('GET', '/ops/design-advisor/catalog', allow=('GET',))
def ops_design_advisor_catalog(handler) -> None:
    handler.send_data(hcc_design_advisor.catalog())


@route('POST', '/ops/design-advisor/recommend', allow=('POST',))
def ops_design_advisor_recommend(handler) -> None:
    payload = handler.read_json_body()
    handler.send_data(
        hcc_design_advisor.recommend(
            page_type=payload.get('page_type'),
            intent=payload.get('intent'),
            visual_profile=payload.get('visual_profile'),
        )
    )

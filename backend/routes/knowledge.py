from __future__ import annotations

from http_api import route
from knowledge_surfaces import knowledge_surfaces


@route('GET', '/ops/memory', allow=('GET',))
def ops_memory(handler) -> None:
    handler.send_data(knowledge_surfaces.memory_summary())


@route('GET', '/ops/skills', allow=('GET',))
def ops_skills(handler) -> None:
    handler.send_data(knowledge_surfaces.skills_summary())


@route('GET', '/ops/files', allow=('GET',))
def ops_files(handler) -> None:
    handler.send_data(knowledge_surfaces.files_summary())


@route('GET', '/ops/profiles', allow=('GET',))
def ops_profiles(handler) -> None:
    handler.send_data(knowledge_surfaces.profiles_summary())


@route('GET', '/ops/gateway', allow=('GET',))
def ops_gateway(handler) -> None:
    handler.send_data(knowledge_surfaces.gateway_summary())

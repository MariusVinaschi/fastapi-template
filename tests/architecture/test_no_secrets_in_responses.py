"""AC-B5: no route's response can expose a stored credential, password, token
or hash.

Only runtime introspection can decide this: a route that opts out of FastAPI's
response_model (``response_model=None``) is not opting out of returning a schema --
``/auth/login`` and ``/auth/refresh`` do exactly this and still return `TokenPair`,
resolved here from the endpoint's own return annotation. Reading source cannot
follow either the response_model or the annotation the way the real objects can.
"""

import typing
from collections.abc import Iterable
from typing import get_args, get_origin

import pytest
from pydantic import BaseModel

pytestmark = pytest.mark.architecture

# Checked as whole underscore-separated segments (`access_token` -> {"access", "token"}),
# not substrings, so "user_id" or "family_id" cannot collide with a real fragment.
SECRET_SEGMENTS = frozenset({"password", "secret", "token", "credential", "credentials", "otp", "hash"})
# Multi-word terms a segment-split would miss ("key" alone is too broad: "primary_key"
# is not a secret).
SECRET_WHOLE_NAMES = frozenset({"api_key", "apikey", "private_key", "recovery_code"})

# AC-05: each entry names the exact (module, class, field) it permits, not the whole
# schema or class name alone -- two identically-named classes in different modules
# must not share an exemption.
EXEMPTIONS: dict[tuple[str, str, str], str] = {
    ("app.domains.users.schemas", "APIKeyGenerated", "api_key"): "returned once, at generation time, by design",
    ("app.domains.users.schemas", "TokenPair", "access_token"): (
        "the bearer token issued to its own owner by /auth/login and /auth/refresh -- the endpoint's entire purpose"
    ),
    ("app.domains.users.schemas", "TokenPair", "refresh_token"): (
        "the refresh token issued to its own owner by /auth/login and /auth/refresh -- the endpoint's entire purpose"
    ),
    ("app.domains.users.schemas", "TokenPair", "token_type"): "a fixed label ('bearer'), not a secret value",
}


def _is_secret_field(name: str) -> bool:
    lowered = name.lower()
    if lowered in SECRET_WHOLE_NAMES:
        return True
    return any(segment in SECRET_SEGMENTS for segment in lowered.split("_"))


def _response_models() -> Iterable[tuple[str, type]]:
    """Every route's effective response type.

    `response_model=None` disables FastAPI's own inference; it does not mean the
    route returns nothing. Resolve the endpoint's return annotation in that case, the
    same way a caller reading the code would.
    """
    from fastapi.routing import APIRoute

    from app.api.router import api_router

    for route in api_router.routes:
        if not isinstance(route, APIRoute):
            continue
        model = route.response_model
        if model is None:
            model = typing.get_type_hints(route.endpoint).get("return")
        if model is not None:
            yield route.path, model


def _nested_models(model: type) -> set[type[BaseModel]]:
    """Every Pydantic model reachable from `model`, including through generics and unions."""
    seen: set[type[BaseModel]] = set()
    stack = [model]
    while stack:
        current = stack.pop()
        origin = get_origin(current)
        if origin is not None:
            stack.extend(get_args(current))
            continue
        if not (isinstance(current, type) and issubclass(current, BaseModel)) or current in seen:
            continue
        seen.add(current)
        for field in current.model_fields.values():
            stack.append(field.annotation)
    return seen


def _is_offending(model: type[BaseModel], field_name: str) -> bool:
    exempt = (model.__module__, model.__qualname__, field_name) in EXEMPTIONS
    return _is_secret_field(field_name) and not exempt


def _offenders(models: Iterable[tuple[str, type]]) -> list[str]:
    """The single code path both the real-tree assertion and its failure control use.

    A regression here (a broken filter, a dead exemption lookup) fails both, so the
    control that proves the sensor CAN fail actually exercises production logic
    instead of a hand-copied reimplementation of it.
    """
    return [
        f"{path} -> {model.__qualname__}.{field_name}"
        for path, response_model in models
        for model in _nested_models(response_model)
        for field_name in model.model_fields
        if _is_offending(model, field_name)
    ]


def test_no_route_response_exposes_a_secret_field():
    offenders = _offenders(_response_models())
    assert not offenders, f"secret field reachable from a response: {offenders}"


def test_a_secret_field_in_a_response_model_is_caught():
    """AC-09: prove `_offenders` -- the real detection path -- can fail, on a fixture."""

    class LeakyRead(BaseModel):
        id: str
        password_hash: str

    offenders = _offenders([("fixture/leaky", LeakyRead)])
    assert offenders == [f"fixture/leaky -> {LeakyRead.__qualname__}.password_hash"]


def test_an_exemption_that_no_longer_applies_is_reported():
    """AC-05: a stale exemption -- naming a field that doesn't exist, or that the
    detector would never flag in the first place -- fails. The second clause is
    what catches an exemption made inert by a change to the detector itself.
    """
    all_fields = {
        (model.__module__, model.__qualname__, name)
        for _, response_model in _response_models()
        for model in _nested_models(response_model)
        for name in model.model_fields
    }
    stale = [target for target in EXEMPTIONS if target not in all_fields]
    assert not stale, f"exemption no longer matches any field: {stale}"

    inert = [target for target in EXEMPTIONS if not _is_secret_field(target[2])]
    assert not inert, f"exemption names a field the detector would never flag: {inert}"

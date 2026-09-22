"""AC-B5: no route's response model can expose a stored credential, password,
token or hash.

Only runtime introspection can decide this: the schemas that hold a secret field
are internal *Create DTOs, never reachable from a route's response_model. Reading
source cannot tell the two apart; resolving the actual FastAPI routes can.
"""

import re
from typing import get_args, get_origin

import pytest
from pydantic import BaseModel

pytestmark = pytest.mark.architecture

SECRET_FIELD = re.compile(r"(password|token|secret)(_|$)|_hash$", re.IGNORECASE)

# AC-05: the one endpoint that returns a freshly generated API key once. Each entry
# names the exact schema and field it permits, not the whole schema.
EXEMPTIONS = {("APIKeyGenerated", "api_key"): "returned once, at generation time, by design"}


def _response_models():
    from fastapi.routing import APIRoute

    from app.api.router import api_router

    for route in api_router.routes:
        if isinstance(route, APIRoute) and route.response_model is not None:
            yield route.path, route.response_model


def _nested_models(model: type) -> set[type[BaseModel]]:
    """Every Pydantic model reachable from `model`, including through generics."""
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


def test_no_route_response_exposes_a_secret_field():
    offenders = []
    for path, response_model in _response_models():
        for model in _nested_models(response_model):
            for name in model.model_fields:
                if SECRET_FIELD.search(name) and EXEMPTIONS.get((model.__name__, name)) is None:
                    offenders.append(f"{path} -> {model.__name__}.{name}")

    assert not offenders, f"secret field reachable from a response: {offenders}"


def test_a_secret_field_in_a_response_model_is_caught():
    """AC-09: prove the sensor can fail, on a fixture model, not the real schemas."""

    class LeakyRead(BaseModel):
        id: str
        password_hash: str

    fields = [name for name in _nested_models(LeakyRead).pop().model_fields if SECRET_FIELD.search(name)]
    assert fields == ["password_hash"]


def test_an_exemption_that_no_longer_applies_is_reported():
    """AC-05: a stale exemption -- naming a schema/field pair that doesn't exist -- fails."""
    all_field_names = {
        (model.__name__, name)
        for _, response_model in _response_models()
        for model in _nested_models(response_model)
        for name in model.model_fields
    }
    stale = [target for target in EXEMPTIONS if target not in all_field_names]

    assert not stale, f"exemption no longer matches any field: {stale}"

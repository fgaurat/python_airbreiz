"""Tout le module est marqué `integration` via la variable `pytestmark`."""

import pytest

pytestmark = pytest.mark.integration


def test_a():
    pass


def test_b(request):
    assert request.node.get_closest_marker("integration") is not None

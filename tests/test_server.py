import pytest

from src.server import get_intro, list_capabilities, search_capabilities


def test_get_intro_returns_portfolio_context():
    intro = get_intro()

    assert "Siemens GBS CEE FPS" in intro
    assert "tailor-made digital solutions" in intro


def test_list_capabilities_returns_known_category():
    capabilities = list_capabilities("toolkit")

    assert "Python" in capabilities
    assert "Mendix" in capabilities


def test_list_capabilities_rejects_unknown_category():
    with pytest.raises(ValueError, match="Unknown category"):
        list_capabilities("math")


def test_search_capabilities_filters_context():
    results = search_capabilities("analytics")

    assert results == {"capabilities": ["finance analytics"], "examples": ["FIN analytics"]}


def test_search_capabilities_rejects_blank_query():
    with pytest.raises(ValueError, match="Query must not be empty"):
        search_capabilities("  ")

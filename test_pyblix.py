import pytest

from pyblix import Gatherer, GatherLevel
from exceptions import InvalidTargetException, InvalidParentLevelException


def test_invalid_target():
    gl = GatherLevel("ul", "id", "articleList")
    with pytest.raises(InvalidTargetException):
        g = Gatherer("pybit.es", True, "https://pybit.es/pages/articles_does_not_exist.html", gl)


def test_invalid_level():
    gl = GatherLevel("x", "id", "nope_nope_nope")
    with pytest.raises(InvalidParentLevelException):
        g = Gatherer("pybit.es", True, "https://pybit.es/pages/articles.html", gl)


def test_verbose(capsys):
    gl = GatherLevel("ul", "id", "articleList")
    g = Gatherer("pybit.es", True, "https://pybit.es/pages/articles.html", gl, verbose=True)
    captures = capsys.readouterr()
    assert "URL" in captures.out
    assert "Validating parent level:" in captures.out


def test_not_verbose(capsys):
    gl = GatherLevel("ul", "id", "articleList")
    g = Gatherer("pybit.es", True, "https://pybit.es/pages/articles.html", gl)
    captures = capsys.readouterr()
    assert "URL" not in captures.out
    assert "Validating parent level:" not in captures.out


def test_valid():
    gl = GatherLevel("ul", "id", "articleList")
    g = Gatherer("pybit.es", True, "https://pybit.es/pages/articles.html", gl)
    assert g.number_of_gather_links > 0


def test_level_to_string():
    gl = GatherLevel("ul", "id", "articleList")
    assert str(gl) == "<ul id='articleList'>"

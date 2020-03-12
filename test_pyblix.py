from exceptions import InvalidParentLevelException, InvalidTargetException

import pytest

from pyblix import Gatherer, GatherLevel
<<<<<<< Updated upstream


def test_invalid_target():
    gl = GatherLevel("ul", "id", "articleList")
    with pytest.raises(InvalidTargetException):
        _ = Gatherer(
            "pybit.es", True, "https://pybit.es/pages/articles_does_not_exist.html", gl
        )
=======
from exceptions import InvalidTargetException, InvalidParentLevelException
from subprocess import Popen
from sys import executable


pid = Popen([executable, 'spawn_test_server.py'], cwd='tests/')

domain = "127.0.0.1:8999"
bad_root = "http://127.0.0.1:8999/simple_website_not_found.html"
good_root = "http://127.0.0.1:8999/simple_website.html"

bad_gl = GatherLevel("x", "x", "x")
good_gl = GatherLevel("ul", "id", "articleList")

use_ssl = False

>>>>>>> Stashed changes

@pytest.mark.parametrize("gatherlevel,domain,root,use_ssl,excep", [(good_gl, domain, bad_root, use_ssl, InvalidTargetException)])
def test_invalid_target(gatherlevel, domain, root, use_ssl, excep):
	with pytest.raises(excep):
		g = Gatherer(domain, use_ssl, root, gatherlevel)

@pytest.mark.parametrize("gatherlevel,domain,root,use_ssl,excep", [(bad_gl, domain, good_root, use_ssl, InvalidParentLevelException)])
def test_invalid_level(gatherlevel, domain, root, use_ssl, excep):
	with pytest.raises(excep):
		g = Gatherer(domain, use_ssl, root, gatherlevel)
		
"""
def test_invalid_level():
    gl = GatherLevel("x", "id", "nope_nope_nope")
    with pytest.raises(InvalidParentLevelException):
        _ = Gatherer("pybit.es", True, "https://pybit.es/pages/articles.html", gl)


def test_verbose(capsys):
    gl = GatherLevel("ul", "id", "articleList")
    g = Gatherer(
        "pybit.es", True, "https://pybit.es/pages/articles.html", gl, verbose=True
    )
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
	
"""
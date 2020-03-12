from exceptions import InvalidParentLevelException, InvalidTargetException

import pytest

from pyblix import Gatherer, GatherLevel
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

@pytest.mark.parametrize("gatherlevel,domain,root,use_ssl,excep", [(good_gl, domain, bad_root, use_ssl, InvalidTargetException)])
def test_invalid_target(gatherlevel, domain, root, use_ssl, excep):
	with pytest.raises(excep):
		g = Gatherer(domain, use_ssl, root, gatherlevel)

@pytest.mark.parametrize("gatherlevel,domain,root,use_ssl,excep", [(bad_gl, domain, good_root, use_ssl, InvalidParentLevelException)])
def test_invalid_level(gatherlevel, domain, root, use_ssl, excep):
	with pytest.raises(excep):
		g = Gatherer(domain, use_ssl, root, gatherlevel)

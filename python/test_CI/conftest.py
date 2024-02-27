import os
import pytest


def pytest_addoption(parser):
    parser.addoption("--ak", default="")
    parser.addoption("--sk", default="")
    parser.addoption("--root-dir", default="")
    parser.addoption("--keywords", default="{}")

@pytest.fixture(scope='session', autouse=True)
def env_set(request):
    if request.config.getoption('--ak') != '':
        os.environ['QIANFAN_ACCESS_KEY'] = request.config.getoption("--ak")
    if request.config.getoption('--sk') != '':
        os.environ['QIANFAN_SECRET_KEY'] = request.config.getoption("--sk")
    if request.config.getoption('--keywords') != '{}':
        os.environ['KEYWORDS_DICT'] = request.config.getoption("--keywords")
    if request.config.getoption('--root-dir') != '':
        os.environ['ROOT_DIR'] = request.config.getoption("--root-dir")
    else:
        os.environ['ROOT_DIR'] = '../..'

    other_env = [('RetryCount', '3'), ('QIANFAN_QPS_LIMIT', '1'), ('QIANFAN_LLM_API_RETRY_COUNT', '3')]
    for key, value in other_env:
        os.environ[key] = value

    yield
    if os.environ.get('QIANFAN_ACCESS_KEY'):
        del os.environ['QIANFAN_ACCESS_KEY']
    if os.environ.get('QIANFAN_SECRET_KEY'):
        del os.environ['QIANFAN_SECRET_KEY']
    if os.environ.get('KEYWORDS_DICT'):
        del os.environ['KEYWORDS_DICT']
    if os.environ.get('ROOT_DIR'):
        del os.environ['ROOT_DIR']
    for key, value in other_env:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="function")
def executor():
    from python.test_CI.utils.cookbook_operate import CookbookExecutor
    with CookbookExecutor() as e:
        yield e

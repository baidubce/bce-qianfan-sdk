def pytest_addoption(parser):
    parser.addoption("--ak", default="")
    parser.addoption("--sk", default="")
    parser.addoption("--root-dir", default="..")
    parser.addoption("--keywords", default="{}")

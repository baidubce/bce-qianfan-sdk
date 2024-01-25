build:
	bash python/scripts/build.sh

install:
	poetry install -E all

uninstall:
	pip uninstall -y qianfan

clean:
	rm -rf build output dist qianfan.egg-info

doc: install
	poetry run bash python/scripts/build_doc.sh

format: install
	poetry run black ./python/qianfan
	poetry run ruff --select I --fix ./python/qianfan

lint: install
	poetry run black ./python/qianfan --check 
	poetry run ruff check ./python/qianfan
	poetry run mypy ./python/qianfan --install-types --non-interactive

test: clean install 
	cd python && bash scripts/run_test.sh

mock: 
	pip install flask
	bash ./python/scripts/run_mock_server.sh

.PHONY: build install uninstall clean 

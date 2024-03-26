build:
	bash ./scripts/build.sh

install:
	poetry install -E all_extension

# install_ntbk:
# 	poetry install -E all

uninstall:
	pip uninstall -y qianfan

clean:
	rm -rf build output dist qianfan.egg-info

doc: install
	poetry run bash ./scripts/build_doc.sh

format: install
	poetry run black ./qianfan
	poetry run ruff --select I --fix ./qianfan

lint: install
	poetry run black ./qianfan --check 
	poetry run ruff check ./qianfan
	poetry run mypy ./qianfan --install-types --non-interactive

test: clean install 
	cd . && bash scripts/run_test.sh

test_ntbk: clean install
	cd . && bash scripts/run_test_ntbk.sh -f "$(func_call)" -r "$(reg)" -p "$(params)"

.PHONY: build install uninstall clean 

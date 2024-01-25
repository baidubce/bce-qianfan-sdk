build: 
	$(MAKE) -C python build

install:
	$(MAKE) -C python install

uninstall:
	pip uninstall -y qianfan

clean:
	rm -rf build output dist qianfan.egg-info

doc: install
	$(MAKE) -C python doc

format: install
	$(MAKE) -C python format

lint: install
	$(MAKE) -C python lint

test: clean install 
	cd python && bash scripts/run_test.sh

mock: 
	pip install flask
	bash ./python/scripts/run_mock_server.sh

gotest:
    $(MAKE) -C go test

.PHONY: build install uninstall clean 

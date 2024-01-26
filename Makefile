prepare_output:
	mkdir -p output

build: prepare_output
	$(MAKE) -C python build
	mv python/output/* ./output
	rm -rf python/output

install:
	$(MAKE) -C python install

uninstall:
	pip uninstall -y qianfan

clean:
	rm -rf output
	$(MAKE) -C python clean

doc: install prepare_output
	$(MAKE) -C python doc
	mv python/output/* ./output
	rm -rf python/output

format: install
	$(MAKE) -C python format

lint: install
	$(MAKE) -C python lint

test: clean install 
	cd python && bash scripts/run_test.sh

mock: 
	bash ./python/scripts/run_mock_server.sh

gotest:
	$(MAKE) -C go test

.PHONY: build install uninstall clean 

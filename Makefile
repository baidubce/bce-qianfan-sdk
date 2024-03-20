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
	rm -rf output/docs
	mv python/output/* ./output
	rm -rf python/output

format: install
	$(MAKE) -C python format

lint: install
	$(MAKE) -C python lint

test: clean install 
	$(MAKE) -C python test
	$(MAKE) -C go test

test_ntbk: clean install
	$(MAKE) -C python test_ntbk func_call=$(func_call) reg=$(reg) params=$(params)

mock: 
	bash ./python/scripts/run_mock_server.sh

.PHONY: build install uninstall clean 

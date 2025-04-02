install:
	uv sync

clean:
	rm -rf dist/

.PHONY: build
build:
	uv build

publish:
	viam module build start --version $(version)

setup:
	./setup.sh

dist/archive.tar.gz: setup
	./build.sh

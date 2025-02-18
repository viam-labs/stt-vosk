install:
	rye sync

bundle:
	tar -czf module.tar.gz *.sh src dist meta.json

upload:
	viam module upload --version $(version) --platform any module.tar.gz

clean:
	rm module.tar.gz && rm -rf dist/

.PHONY: build
build:
	rye build

publish: build bundle upload clean

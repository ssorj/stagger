.PHONY: build
build:
	@mkdir -p build
	transom --quiet --site-url "http://localhost:8080" render --force static build/static
	ln -snf ../python build/python

.PHONY: test
test:
	scripts/test

.PHONY: clean
clean:
	rm -rf build

.PHONY: run
run:
	cd build && python3 python/app.py

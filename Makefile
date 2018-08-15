.PHONY: build
build:
	scripts/smoke-test

.PHONY: run
run:
	python3 app.py

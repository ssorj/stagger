.PHONY: test
test:
	scripts/test

.PHONY: run
run:
	python3 server/app.py

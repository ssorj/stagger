#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

.NOTPARALLEL:

DESTDIR := ""
PREFIX := ${HOME}/.local
INSTALLED_STAGGER_HOME = ${PREFIX}/share/stagger

export STAGGER_HOME = ${CURDIR}/build
export PATH := ${STAGGER_HOME}/bin:${PATH}
export PYTHONPATH := ${CURDIR}/python:${PYTHONPATH}

BIN_SOURCES := $(shell find bin -type f -name \*.in)
BIN_TARGETS := ${BIN_SOURCES:%.in=build/%}

.PHONY: default
default: build

.PHONY: help
help:
	@echo "build          Build the code"
	@echo "install        Install the code"
	@echo "clean          Clean up the source tree"
	@echo "test           Run the tests"
	@echo "run            Run the server"

.PHONY: clean
clean:
	rm -rf python/__pycache__ python/stagger/__pycache__
	rm -rf build

.PHONY: build
build: ${BIN_TARGETS} build/prefix.txt
	python3 -m transom render --quiet --site-url "" --force static build/static
	ln -snf ../python build/python

.PHONY: install
install: build
	scripts/install-files build/bin ${DESTDIR}$$(cat build/prefix.txt)/bin
	scripts/install-files python/stagger ${DESTDIR}$$(cat build/prefix.txt)/share/stagger/python/stagger
	scripts/install-files build/static ${DESTDIR}$$(cat build/prefix.txt)/share/stagger/static

.PHONY: test
test: build
	scripts/test

.PHONY: run
run: build
	STAGGER_HTTP_PORT=9090 stagger

.PHONY: build-image
build-image:
	sudo docker build -t ssorj/stagger .

.PHONY: run-image
run-image:
	sudo docker run -p 8080:8080 ssorj/stagger

.PHONY: push-image
push-image:
	sudo docker push ssorj/stagger

# oc tag --source=docker ssorj/stagger:latest stagger:latest

build/prefix.txt:
	echo ${PREFIX} > build/prefix.txt

build/bin/%: bin/%.in
	scripts/configure-file -a stagger_home=${INSTALLED_STAGGER_HOME} $< $@

.PHONY: update-%
update-%:
	curl "https://raw.githubusercontent.com/ssorj/$*/master/python/$*.py" -o python/$*.py

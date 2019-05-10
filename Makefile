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
INSTALL_DIR := ${HOME}/.local/opt/stagger
IMAGE_NAME := quay.io/ssorj/stagger

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
	rm -rf python/__pycache__ python/stagger/__pycache__ scripts/__pycache__
	rm -rf build

.PHONY: build
build: ${BIN_TARGETS} build/install-dir.txt
	python3 -m transom render --quiet --site-url "" --force static build/static
	ln -snf ../python build/python

.PHONY: install
install: build
	scripts/install-files build/bin ${DESTDIR}$$(cat build/install-dir.txt)/bin
	scripts/install-files python ${DESTDIR}$$(cat build/install-dir.txt)/python
	scripts/install-files python/stagger ${DESTDIR}$$(cat build/install-dir.txt)/python/stagger
	scripts/install-files build/static ${DESTDIR}$$(cat build/install-dir.txt)/static

.PHONY: test
test: build
	stagger-test

.PHONY: run
run: build
	STAGGER_HTTP_URL=https://example.net:8080 STAGGER_AMQP_URL=amqps://example.net:5672 stagger

.PHONY: build-image
build-image:
	podman build --no-cache -qt ${IMAGE_NAME} .

.PHONY: test-image
test-image:
	podman run --rm -it ${IMAGE_NAME} /app/bin/stagger-test

.PHONY: run-image
run-image:
	podman run --rm -p 8080:8080 ${IMAGE_NAME}

.PHONY: debug-image
debug-image:
	podman run --rm -p 8080:8080 -it ${IMAGE_NAME} /bin/bash

# Prerequisite: podman login quay.io

.PHONY: push-image
push-image:
	podman push -q ${IMAGE_NAME}

# To tell the cluster about the new image:
# oc tag --source=docker ${IMAGE_NAME} stagger

build/install-dir.txt:
	echo ${INSTALL_DIR} > build/install-dir.txt

build/bin/%: bin/%.in
	scripts/configure-file -a stagger_home=${INSTALL_DIR} $< $@

.PHONY: update-%
update-%:
	curl "https://raw.githubusercontent.com/ssorj/$*/master/python/$*.py" -o python/$*.py

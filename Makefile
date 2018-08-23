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

export PATH := ${CURDIR}/build/bin:${PATH}
export PYTHONPATH := ${CURDIR}/python:${PYTHONPATH}

.PHONY: build
build:
	@mkdir -p build
	python3 -m transom --quiet render --site-url "" --force static build/static
	ln -snf ../python build/python

.PHONY: test
test: build
	scripts/test

.PHONY: clean
clean:
	rm -rf python/__pycache__
	rm -rf build

.PHONY: run
run: build
	cd build && python3 python/app.py

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

.PHONY: update-%
update-%:
	curl "https://raw.githubusercontent.com/ssorj/$*/master/python/$*.py" -o python/$*.py

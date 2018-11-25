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

FROM fedora
MAINTAINER Justin Ross <jross@apache.org>

RUN dnf -qy --setopt deltarpm=0 install gcc make python3-devel python3-qpid-proton redhat-rpm-config \
 && dnf -q clean all

COPY . /home/app
RUN useradd --user-group --no-create-home app && chown -R app:app /home/app
USER app
WORKDIR /home/app/

RUN pip3 install --user starlette uvicorn aiofiles
RUN make clean build install

ENV PATH=/home/app/.local/bin:$PATH
CMD ["stagger"]

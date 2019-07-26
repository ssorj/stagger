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

FROM registry.fedoraproject.org/fedora-minimal AS build

RUN microdnf --nodocs install make findutils gcc python3-devel && microdnf clean all

COPY . /src
RUN mkdir /app
ENV HOME=/app

RUN pip3 install --user starlette uvicorn aiofiles

WORKDIR /src
RUN make clean install INSTALL_DIR=/app
RUN chmod -R 775 /app

FROM registry.fedoraproject.org/fedora-minimal

RUN microdnf --nodocs install python3-qpid-proton python3-requests python3-ujson qtools && microdnf clean all

COPY --from=build /app /app

WORKDIR /app
ENV HOME=/app
ENV PATH=$HOME/bin:$PATH

EXPOSE 8080
EXPOSE 5672

CMD ["stagger"]

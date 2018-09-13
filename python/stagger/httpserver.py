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

import binascii as _binascii
import json as _json
import json.decoder as _json_decoder
import logging as _logging
import os as _os
import uvicorn as _uvicorn

from .model import *
from starlette import *
from starlette.routing import *
from starlette.staticfiles import *

_log = _logging.getLogger("httpserver")

__all__ = ["HttpServer"]

class HttpServer:
    def __init__(self, app, host="0.0.0.0", port=8080):
        self.app = app
        self.host = host
        self.port = port

        routes = [
            Path("/api/data/?",
                 app=_serve_data, methods=["GET", "HEAD"]),
            Path("/api/repos/{repo_id}/?",
                 app=_serve_repo, methods=["PUT", "DELETE", "GET", "HEAD"]),
            Path("/api/repos/{repo_id}/tags/{tag_id}/?",
                 app=_serve_tag, methods=["PUT", "DELETE", "GET", "HEAD"]),
            Path("/api/repos/{repo_id}/tags/{tag_id}/artifacts/{artifact_id}/?",
                 app=_serve_artifact, methods=["PUT", "DELETE", "GET", "HEAD"]),
            Path("/", StaticFile(path=_os.path.join(self.app.home, "static", "index.html"))),
            PathPrefix("", StaticFiles(directory=_os.path.join(self.app.home, "static"))),
        ]

        self._router = _Router(self.app, routes)

    def run(self):
        _uvicorn.run(self._router, self.host, self.port, log_level="warning")

class _Router(Router):
    def __init__(self, app, routes):
        super().__init__(routes)
        self.app = app

    def __call__(self, scope):
        scope["app"] = self.app
        return super().__call__(scope)

class _NotFoundResponse(PlainTextResponse):
    def __init__(exception):
        message = f"Not found: {exception}"
        super().__init__(message, 404)
        print(message)

class _NotModifiedResponse(PlainTextResponse):
    def __init__(exception):
        message = "Not modified"
        super().__init__(message, 304)
        print(message)

class _BadJsonResponse(PlainTextResponse):
    def __init__(exception):
        message = f"Bad request: Failure decoding JSON: {exception}"
        super().__init__(message, 400)
        print(message)

class _BadDataResponse(PlainTextResponse):
    def __init__(exception):
        message = f"Bad request: Illegal data: {exception}"
        super().__init__(message, 400)
        print(message)

@asgi_application
async def _serve_data(request):
    model = request["app"].model

    server_etag = str(model.revision)
    client_etag = request.headers.get("If-None-Match")

    if client_etag is not None and client_etag == server_etag:
        return _NotModifiedResponse()

    if request.method == "GET":
        response = JSONResponse(model.data())
        response.headers["ETag"] = f"\"{model.revision}\""
        return response

    if request.method == "HEAD":
        response = Response("")
        response.headers["ETag"] = f"\"{model.revision}\""
        return response

@asgi_application
async def _serve_repo(request):
    model = request["app"].model
    repo_id = request["kwargs"]["repo_id"]

    if request.method == "PUT":
        try:
            repo_data = await request.json()
        except _json_decoder.JSONDecodeError as e:
            return _BadJsonResponse(e)

        try:
            model.put_repo(repo_id, repo_data)
        except DataError as e:
            return _BadDataResponse(e)

        return Response("")

    if request.method == "DELETE":
        try:
            model.delete_repo(repo_id)
        except KeyError as e:
            return _NotFoundResponse(e)

        return Response("")

    try:
        repo = model.repos[repo_id]
    except KeyError as e:
        return _NotFoundResponse(e)

    server_etag = str(repo.digest)
    client_etag = request.headers.get("If-None-Match")

    if client_etag is not None and client_etag == server_etag:
        return _NotModifiedResponse()

    if request.method == "GET":
        response = JSONResponse(repo.data())
        response.headers["ETag"] = f"\"{repo.digest}\""
        return response

    if request.method == "HEAD":
        response = Response("")
        response.headers["ETag"] = f"\"{repo.digest}\""
        return response

@asgi_application
async def _serve_tag(request):
    model = request["app"].model
    repo_id = request["kwargs"]["repo_id"]
    tag_id = request["kwargs"]["tag_id"]

    if request.method == "PUT":
        try:
            tag_data = await request.json()
        except _json_decoder.JSONDecodeError as e:
            return _BadJsonResponse(e)

        try:
            model.put_tag(repo_id, tag_id, tag_data)
        except DataError as e:
            return _BadDataResponse(e)

        return Response("")

    if request.method == "DELETE":
        try:
            model.delete_tag(repo_id, tag_id)
        except KeyError as e:
            return _NotFoundResponse(e)

        return Response("")

    try:
        tag = model.repos[repo_id].tags[tag_id]
    except KeyError as e:
        return _NotFoundResponse(e)

    server_etag = str(tag.digest)
    client_etag = request.headers.get("If-None-Match")

    if client_etag is not None and client_etag == server_etag:
        return _NotModifiedResponse()

    if request.method == "GET":
        response = JSONResponse(tag.data())
        response.headers["ETag"] = f"\"{tag.digest}\""
        return response

    if request.method == "HEAD":
        response = Response("")
        response.headers["ETag"] = f"\"{tag.digest}\""
        return response

@asgi_application
async def _serve_artifact(request):
    model = request["app"].model
    repo_id = request["kwargs"]["repo_id"]
    tag_id = request["kwargs"]["tag_id"]
    artifact_id = request["kwargs"]["artifact_id"]

    if request.method == "PUT":
        try:
            artifact_data = await request.json()
        except _json_decoder.JSONDecodeError as e:
            return _BadJsonResponse(e)

        try:
            model.put_artifact(repo_id, tag_id, artifact_id, artifact_data)
        except DataError as e:
            return _BadDataResponse(e)

        return Response("")

    if request.method == "DELETE":
        try:
            model.delete_artifact(repo_id, tag_id, artifact_id)
        except KeyError as e:
            return _NotFoundResponse(e)

        return Response("")

    try:
        artifact = model.repos[repo_id].tags[tag_id].artifacts[artifact_id]
    except KeyError as e:
        return _NotFoundResponse(e)

    server_etag = str(artifact.digest)
    client_etag = request.headers.get("If-None-Match")

    if client_etag is not None and client_etag == server_etag:
        return _NotModifiedResponse()

    if request.method == "GET":
        response = JSONResponse(artifact.data())
        response.headers["ETag"] = f"\"{artifact.digest}\""
        return response

    if request.method == "HEAD":
        response = Response("")
        response.headers["ETag"] = f"\"{artifact.digest}\""
        return response

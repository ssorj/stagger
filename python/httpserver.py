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

import json.decoder as _json_decoder
import logging as _logging
import os as _os
import uvicorn as _uvicorn

from data import *
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
            Path("/api/repos/?",
                 app=_serve_repo_index, methods=["GET"]),
            Path("/api/repos/{repo_id}/?",
                 app=_serve_repo, methods=["PUT", "GET", "DELETE"]),
            Path("/api/repos/{repo_id}/tags/?",
                 app=_serve_tag_index, methods=["GET"]),
            Path("/api/repos/{repo_id}/tags/{tag_id}/?",
                 app=_serve_tag, methods=["PUT", "GET", "DELETE"]),
            Path("/api/repos/{repo_id}/tags/{tag_id}/artifacts/?",
                 app=_serve_artifact_index, methods=["GET"]),
            Path("/api/repos/{repo_id}/tags/{tag_id}/artifacts/{artifact_id}/?",
                 app=_serve_artifact, methods=["GET"]),
            Path("/", StaticFile(path="static/index.html")),
            PathPrefix("", StaticFiles(directory="static")),
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
async def _serve_repo_index(request):
    data = request["app"].data
    return JSONResponse(data.repos)

@asgi_application
async def _serve_repo(request):
    data = request["app"].data
    repo_id = request["kwargs"]["repo_id"]

    if request.method == "GET":
        try:
            tag = data.repos[repo_id]
        except KeyError as e:
            return _NotFoundResponse(e)

        return JSONResponse(repo)

    if request.method == "PUT":
        try:
            repo = Repo(**await request.json())
        except _json_decoder.JSONDecodeError as e:
            return _BadJsonResponse(e)
        except DataError as e:
            return _BadDataResponse(e)

        data.put_repo(repo_id, repo)

        return Response("")

    if request.method == "DELETE":
        try:
            data.delete_repo(repo_id)
        except KeyError as e:
            return _NotFoundResponse(e)

        return Response("")

@asgi_application
async def _serve_tag_index(request):
    data = request["app"].data
    repo_id = request["kwargs"]["repo_id"]

    try:
        repo = data.repos[repo_id]
    except KeyError as e:
        return _NotFoundResponse(e)

    return JSONResponse(repo.tags)

@asgi_application
async def _serve_tag(request):
    data = request["app"].data
    repo_id = request["kwargs"]["repo_id"]
    tag_id = request["kwargs"]["tag_id"]

    if request.method == "PUT":
        try:
            tag = Tag(**await request.json())
        except _json_decoder.JSONDecodeError as e:
            return _BadJsonResponse(e)
        except DataError as e:
            return _BadDataResponse(e)

        data.put_tag(repo_id, tag_id, tag)

        return Response("")

    if request.method == "GET":
        try:
            tag = data.repos[repo_id].tags[tag_id]
        except KeyError as e:
            return _NotFoundResponse(e)

        return JSONResponse(tag)

    if request.method == "DELETE":
        try:
            data.delete_tag(repo_id, tag_id)
        except KeyError as e:
            return _NotFoundResponse(e)

        return Response("")

@asgi_application
async def _serve_artifact_index(request):
    data = request["app"].data
    repo_id = request["kwargs"]["repo_id"]
    tag_id = request["kwargs"]["tag_id"]

    try:
        artifacts = data.repos[repo_id].tags[tag_id].artifacts
    except KeyError as e:
        return _NotFoundResponse(e)

    return JSONResponse(artifacts)

@asgi_application
async def _serve_artifact(request):
    data = request["app"].data
    repo_id = request["kwargs"]["repo_id"]
    tag_id = request["kwargs"]["tag_id"]
    artifact_id = request["kwargs"]["artifact_id"]

    try:
        artifact = data.repos[repo_id].tags[tag_id].artifacts[artifact_id]
    except KeyError as e:
        return _NotFoundResponse(e)

    return JSONResponse(artifact)

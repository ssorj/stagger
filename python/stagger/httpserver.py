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

import json as _json
import json.decoder as _json_decoder
import logging as _logging
import os as _os
import uvicorn as _uvicorn

from .model import *
from starlette.requests import *
from starlette.responses import *
from starlette.routing import *
from starlette.staticfiles import *

_log = _logging.getLogger("httpserver")

__all__ = ["HttpServer"]

class _HttpServer:
    def __init__(self, app, host="0.0.0.0", port=8080):
        self.app = app
        self.host = host
        self.port = port

        routes = [
            Route("/api/data",
                  endpoint=_DataHandler, methods=["GET", "HEAD"]),
            Route("/api/repos/{repo_id}",
                  endpoint=_RepoHandler, methods=["PUT", "DELETE", "GET", "HEAD"]),
            Route("/api/repos/{repo_id}/tags/{tag_id}",
                  endpoint=_TagHandler, methods=["PUT", "DELETE", "GET", "HEAD"]),
            Route("/api/repos/{repo_id}/tags/{tag_id}/artifacts/{artifact_id}",
                  endpoint=_ArtifactHandler, methods=["PUT", "DELETE", "GET", "HEAD"]),
            Route("/", endpoint=_IndexHandler, methods=["GET", "HEAD"]),
            Mount("", app=StaticFiles(directory=_os.path.join(self.app.home, "static"))),
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
    def __init__(self, exception):
        message = f"Not found: {exception}"
        super().__init__(message, 404)
        print(message)

class _NotModifiedResponse(PlainTextResponse):
    def __init__(self, exception):
        message = "Not modified"
        super().__init__(message, 304)
        print(message)

class _BadJsonResponse(PlainTextResponse):
    def __init__(self, exception):
        message = f"Bad request: Failure decoding JSON: {exception}"
        super().__init__(message, 400)
        print(message)

class _BadDataResponse(PlainTextResponse):
    def __init__(self, exception):
        message = f"Bad request: Illegal data: {exception}"
        super().__init__(message, 400)
        print(message)

class _AsgiHandler:
    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        request = Request(self.scope, receive)
        request.app = request["app"]

        response = await self.process(request)

        if response is not None:
            await response(receive, send)
            return

        server_etag = self.etag(request)
        client_etag = request.headers.get("If-None-Match")

        if client_etag is not None and server_etag is not None:
            if client_etag == server_etag:
                response = _NotModifiedResponse()
                await response(receive, send)
                return

        response = await self.render(request)

        assert response is not None

        if server_etag is not None:
            response.headers["ETag"] = f'"{server_etag}"'

        await response(receive, send)

    async def process(self, request):
        if request.method == "HEAD":
            return Response("")

    def etag(self, request):
        pass

    async def render(self, request):
        pass

class _IndexHandler(_AsgiHandler):
    _etag = id(1) # XXX

    def etag(self, request):
        return self._etag

    async def render(self, request):
        return FileResponse(path=_os.path.join(request.app.home, "static", "index.html"))

class _DataHandler(_AsgiHandler):
    def etag(self, request):
        return str(request.app.model.revision)

    async def render(self, request):
        return JSONResponse(request.app.model.data())

class _RepoHandler(_AsgiHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]

        if request.method == "PUT":
            try:
                repo_data = await request.json()
            except _json_decoder.JSONDecodeError as e:
                return _BadJsonResponse(e)

            try:
                model.put_repo(repo_id, repo_data)
            except (DataError, TypeError) as e:
                return _BadDataResponse(e)

            return Response("OK\n")

        if request.method == "DELETE":
            try:
                model.delete_repo(repo_id)
            except KeyError as e:
                return _NotFoundResponse(e)

            return Response("OK\n")

        if request.method == "HEAD":
            return Response("")

        try:
            request.repo = model.repos[repo_id]
        except KeyError as e:
            return _NotFoundResponse(e)

    def etag(self, request):
        return str(request.repo._digest)

    async def render(self, request):
        return JSONResponse(request.repo.data())

class _TagHandler(_AsgiHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]
        tag_id = request.path_params["tag_id"]

        if request.method == "PUT":
            try:
                tag_data = await request.json()
            except _json_decoder.JSONDecodeError as e:
                return _BadJsonResponse(e)

            try:
                model.put_tag(repo_id, tag_id, tag_data)
            except (DataError, TypeError) as e:
                return _BadDataResponse(e)

            return Response("OK\n")

        if request.method == "DELETE":
            try:
                model.delete_tag(repo_id, tag_id)
            except KeyError as e:
                return _NotFoundResponse(e)

            return Response("OK\n")

        if request.method == "HEAD":
            return Response("")

        try:
            request.tag = model.repos[repo_id].tags[tag_id]
        except KeyError as e:
            return _NotFoundResponse(e)

    def etag(self, request):
        return str(request.tag._digest)

    async def render(self, request):
        return JSONResponse(request.tag.data())

class _ArtifactHandler(_AsgiHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]
        tag_id = request.path_params["tag_id"]
        artifact_id = request.path_params["artifact_id"]

        if request.method == "PUT":
            try:
                artifact_data = await request.json()
            except _json_decoder.JSONDecodeError as e:
                return _BadJsonResponse(e)

            try:
                model.put_artifact(repo_id, tag_id, artifact_id, artifact_data)
            except (DataError, TypeError) as e:
                return _BadDataResponse(e)

            return Response("OK\n")

        if request.method == "DELETE":
            try:
                model.delete_artifact(repo_id, tag_id, artifact_id)
            except KeyError as e:
                return _NotFoundResponse(e)

            return Response("OK\n")

        if request.method == "HEAD":
            return Response("")

        try:
            request.artifact = model.repos[repo_id].tags[tag_id].artifacts[artifact_id]
        except KeyError as e:
            return _NotFoundResponse(e)

    def etag(self, request):
        return str(request.artifact._digest)

    async def render(self, request):
        return JSONResponse(request.artifact.data())

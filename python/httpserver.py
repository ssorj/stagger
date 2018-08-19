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
            Path("/api/tags/?", app=_serve_tag_index, methods=["GET"]),
            Path("/api/tags/{tag_id}/?", app=_serve_tag, methods=["PUT", "GET", "DELETE"]),
            Path("/api/tags/{tag_id}/artifacts/?", app=_serve_artifact_index, methods=["GET"]),
            Path("/api/tags/{tag_id}/artifacts/{artifact_name}/?", app=_serve_artifact, methods=["GET"]),
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

_not_found = Response("Not found", 404, media_type="text/plain")

@asgi_application
async def _serve_tag_index(request):
    data = request["app"].data
    return JSONResponse(data.tags)

@asgi_application
async def _serve_tag(request):
    data = request["app"].data
    tag_id = request["kwargs"]["tag_id"]

    if request.method == "GET":
        try:
            tag = data.tags[tag_id]
        except KeyError:
            return _not_found

        return JSONResponse(tag)

    if request.method == "PUT":
        try:
            tag = Tag(**await request.json())
        except _json_decoder.JSONDecodeError as e:
            return Response(f"Bad request: Failure decoding JSON: {e}", 400,
                            media_type="text/plain")
        except DataError as e:
            return Response(f"Bad request: {e}", 400, media_type="text/plain")

        data.put_tag(tag)

        return Response("")

    if request.method == "DELETE":
        try:
            data.delete_tag(tag_id)
        except KeyError:
            return _not_found

        return Response("")

@asgi_application
async def _serve_artifact_index(request):
    data = request["app"].data
    tag_id = request["kwargs"]["tag_id"]

    try:
        content = data.tags[tag_id]["artifacts"]
    except KeyError:
        return _not_found

    return JSONResponse(content)

@asgi_application
async def _serve_artifact(request):
    data = request["app"].data
    tag_id = request["kwargs"]["tag_id"]
    artifact_name = request["kwargs"]["artifact_name"]

    try:
        content = data.tags[tag_id]["artifacts"][artifact_name]
    except KeyError:
        return _not_found

    return JSONResponse(content)